import asyncio

from app.analysis.classify import auto_category, resolve_category
from app.analysis.decision import decide
from app.analysis.fair_price import compute_fair_price, compute_technical
from app.models import (
    AssetType,
    PortfolioEvaluationRequest,
    PortfolioEvaluationResponse,
    PortfolioItem,
    PortfolioPosition,
    PortfolioSnapshot,
    PortfolioStateResponse,
    SavePortfolioRequest,
    StoredPortfolioItem,
)
from app.repositories import AssetRepository, PortfolioRepository


class PortfolioService:
    def __init__(self):
        self.asset_repo = AssetRepository()
        self.portfolio_repo = PortfolioRepository()

    async def evaluate_portfolio(
        self, req: PortfolioEvaluationRequest
    ) -> PortfolioEvaluationResponse:
        if not req.items:
            raise ValueError("Carteira vazia.")

        async def _one(item: PortfolioItem) -> PortfolioPosition:

            if item.ticker.startswith("RF_"):
                invested = round(item.quantity * item.avg_price, 2)
                return PortfolioPosition(
                    ticker=item.ticker.upper(),
                    name="Renda Fixa",
                    asset_type=AssetType.br_stock,
                    quantity=item.quantity,
                    avg_price=item.avg_price,
                    current_price=item.avg_price,
                    invested=invested,
                    current_value=invested,
                    pnl=0.0,
                    pnl_pct=0.0,
                    fair_price=None,
                    margin_of_safety=None,
                    verdict="HOLD",
                    label="Renda Fixa",
                    reasons=["Investimento em renda fixa"],
                    category="renda_fixa",
                    category_resolved="renda_fixa",
                    dividend_yield=None,
                    sector="Renda Fixa",
                )

            try:
                snap = await self.asset_repo.get_asset(item.ticker)
            except Exception:
                snap = None

            if not snap:
                return PortfolioPosition(
                    ticker=item.ticker.upper(),
                    name=None,
                    asset_type=AssetType.br_stock,
                    quantity=item.quantity,
                    avg_price=item.avg_price,
                    current_price=None,
                    invested=round(item.quantity * item.avg_price, 2),
                    current_value=None,
                    pnl=None,
                    pnl_pct=None,
                    fair_price=None,
                    margin_of_safety=None,
                    verdict="UNKNOWN",
                    label="Sem dados",
                    reasons=[f"Não conseguimos coletar dados de {item.ticker}."],
                    category=item.category,
                    category_resolved=resolve_category(item.category, "trade"),
                )

            history, dividends = await asyncio.gather(
                self.asset_repo.get_history(item.ticker, period="2y"),
                self.asset_repo.get_dividends(item.ticker),
            )

            fair = compute_fair_price(
                price=snap.price,
                eps=snap.eps,
                book_value=snap.book_value,
                dividends=dividends,
                asset_type=snap.asset_type,
                week52_high=snap.fifty_two_week_high,
            )

            tech = compute_technical(history, snap.fifty_two_week_high, snap.fifty_two_week_low)
            dec = decide(fair, tech, current_price=snap.price, avg_cost=item.avg_price)

            invested = item.quantity * item.avg_price
            current = (snap.price or 0) * item.quantity if snap.price else None
            pnl = (current - invested) if current is not None else None
            pnl_pct = (pnl / invested * 100) if (pnl is not None and invested > 0) else None

            auto = auto_category(snap.asset_type, snap.dividend_yield, bool(dividends))

            return PortfolioPosition(
                ticker=snap.symbol,
                name=snap.name,
                asset_type=AssetType(snap.asset_type),
                quantity=item.quantity,
                avg_price=round(item.avg_price, 4),
                current_price=round(snap.price, 4) if snap.price else None,
                invested=round(invested, 2),
                current_value=round(current, 2) if current is not None else None,
                pnl=round(pnl, 2) if pnl is not None else None,
                pnl_pct=round(pnl_pct, 2) if pnl_pct is not None else None,
                fair_price=fair.consensus,
                margin_of_safety=fair.margin_of_safety,
                verdict=dec.verdict,
                label=dec.label,
                reasons=dec.reasons,
                category=item.category,
                category_resolved=resolve_category(item.category, auto),
                dividend_yield=snap.dividend_yield,
                sector=snap.sector,
            )

        positions = [p for p in await asyncio.gather(*[_one(i) for i in req.items]) if p]

        total_inv = sum(p.invested for p in positions)
        total_cur = sum(p.current_value or p.invested for p in positions)
        total_pnl = total_cur - total_inv
        total_pnl_pct = (total_pnl / total_inv * 100) if total_inv > 0 else 0.0

        if any(p.current_value is not None for p in positions):
            try:
                self.portfolio_repo.record_snapshot(
                    total_invested=round(total_inv, 2),
                    total_current=round(total_cur, 2),
                    total_pnl=round(total_pnl, 2),
                    total_pnl_pct=round(total_pnl_pct, 2),
                )
            except Exception:
                pass

        return PortfolioEvaluationResponse(
            positions=positions,
            total_invested=round(total_inv, 2),
            total_current=round(total_cur, 2),
            total_pnl=round(total_pnl, 2),
            total_pnl_pct=round(total_pnl_pct, 2),
        )

    def get_portfolio(self) -> PortfolioStateResponse:
        items = self.portfolio_repo.list_positions()
        snaps = self.portfolio_repo.list_snapshots(limit=90)

        return PortfolioStateResponse(
            items=[StoredPortfolioItem(**i) for i in items],
            last_updated=self.portfolio_repo.last_updated(),
            snapshots=[PortfolioSnapshot(**s) for s in snaps],
        )

    def save_portfolio(self, req: SavePortfolioRequest) -> PortfolioStateResponse:
        self.portfolio_repo.replace_all(
            [
                {
                    "ticker": i.ticker,
                    "quantity": i.quantity,
                    "avg_price": i.avg_price,
                    "category": i.category or "auto",
                }
                for i in req.items
            ]
        )

        items = self.portfolio_repo.list_positions()
        snaps = self.portfolio_repo.list_snapshots(limit=90)

        return PortfolioStateResponse(
            items=[StoredPortfolioItem(**i) for i in items],
            last_updated=self.portfolio_repo.last_updated(),
            snapshots=[PortfolioSnapshot(**s) for s in snaps],
        )

    def delete_position(self, ticker: str) -> dict:
        self.portfolio_repo.delete_position(ticker)
        return {"deleted": ticker.upper()}

    async def refresh_portfolio(self) -> PortfolioEvaluationResponse:
        items = self.portfolio_repo.list_positions()
        if not items:
            raise ValueError("Nenhuma carteira salva ainda.")

        req = PortfolioEvaluationRequest(
            items=[
                PortfolioItem(
                    ticker=i["ticker"],
                    quantity=i["quantity"],
                    avg_price=i["avg_price"],
                    category=i.get("category", "auto"),
                )
                for i in items
            ],
        )

        return await self.evaluate_portfolio(req)
