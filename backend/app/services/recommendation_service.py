from app.analysis.scoring import rank
from app.core.config import get_settings
from app.llm.gemini_client import explain_portfolio
from app.models import (
    OptimizationStrategy,
    RecommendRequest,
    RecommendResponse,
    ScoredCompany,
)
from app.optimizer.allocator import allocate
from app.optimizer.portfolio import optimize_portfolio, portfolio_metrics
from app.repositories import AssetRepository


class RecommendationService:
    def __init__(self):
        self.asset_repo = AssetRepository()

    async def recommend(self, req: RecommendRequest) -> RecommendResponse:
        settings = get_settings()
        tickers = req.universe or settings.universe

        if not tickers:
            raise ValueError("Universo vazio.")

        companies = await self.asset_repo.get_universe(tickers)
        if not companies:
            raise ValueError("Não foi possível obter dados de nenhum ativo.")

        ranked: list[ScoredCompany] = rank(companies, req.profile, req.exclude_sectors)

        allocations = None
        history: dict = {}

        if req.strategy != OptimizationStrategy.score_weighted:
            history = await self.asset_repo.get_b3_history(
                [s.fundamentals.ticker for s in ranked[: req.max_positions]]
            )
            allocations = optimize_portfolio(
                ranked, history, req.cash, req.max_positions, strategy=req.strategy.value
            )

        if not allocations:
            allocations = allocate(ranked, req.cash, req.max_positions)

        if not history and allocations:
            history = await self.asset_repo.get_b3_history([a.ticker for a in allocations])

        metrics = portfolio_metrics(allocations, history) if allocations else {}
        invested = sum(a.invested for a in allocations)

        explanation = ""
        if req.explain:
            explanation = explain_portfolio(allocations, req.profile, metrics)

        return RecommendResponse(
            profile=req.profile,
            strategy=req.strategy,
            cash_input=round(req.cash, 2),
            cash_invested=round(invested, 2),
            cash_remaining=round(req.cash - invested, 2),
            allocations=allocations,
            metrics=metrics,
            explanation=explanation,
        )

    async def analyze(self, req: RecommendRequest) -> dict:
        settings = get_settings()
        tickers = req.universe or settings.universe
        companies = await self.asset_repo.get_universe(tickers)
        ranked = rank(companies, req.profile, req.exclude_sectors)

        return {
            "profile": req.profile,
            "count": len(ranked),
            "ranking": [r.model_dump() for r in ranked],
        }
