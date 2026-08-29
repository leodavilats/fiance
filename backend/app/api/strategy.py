from fastapi import APIRouter, Depends

from app import affirmation
from app.entitlement import Feature, requires
from app.models import PortfolioItem
from app.repositories import PortfolioRepository
from app.services import (
    FixedIncomeService,
    GoalService,
    OpportunityService,
    PortfolioService,
    StrategyService,
)

router = APIRouter()

strategy_service = StrategyService()
opportunity_service = OpportunityService()
portfolio_service = PortfolioService()
portfolio_repo = PortfolioRepository()
goal_service = GoalService()
fixed_income_service = FixedIncomeService()


def _renda_fixa_como_posicoes() -> list:
    return fixed_income_service.as_portfolio_positions()


@router.get("/strategy", dependencies=[Depends(requires(Feature.STRATEGY))])
async def get_investment_strategy(cash_available: float = 0.0) -> dict:
    cash = cash_available

    stored = portfolio_repo.list_positions()
    current_portfolio = [
        PortfolioItem(
            ticker=i["ticker"],
            quantity=i["quantity"],
            avg_price=i["avg_price"],
            category=i.get("category", "auto"),
        )
        for i in stored
    ]

    rf_positions = _renda_fixa_como_posicoes()

    goals = goal_service.get_goals()

    opps_resp = await opportunity_service.get_opportunities(
        include_held=False,
        page=1,
        page_size=50,
        sort_by="score",
        sort_order="desc",
    )

    portfolio_evaluation = None
    if stored or rf_positions:
        posicoes = []
        totais = {"invested": 0.0, "current": 0.0, "pnl": 0.0, "pnl_pct": 0.0}
        if stored:
            eval_resp = await portfolio_service.evaluate_stored_for_current_user()
            posicoes = [p.model_dump() for p in eval_resp.positions]
            totais = {
                "invested": eval_resp.total_invested,
                "current": eval_resp.total_current,
                "pnl": eval_resp.total_pnl,
                "pnl_pct": eval_resp.total_pnl_pct,
            }
        posicoes += [p.model_dump() for p in rf_positions]
        portfolio_evaluation = {
            "positions": posicoes,
            "total_invested": totais["invested"] + sum(p.invested for p in rf_positions),
            "total_current": totais["current"]
            + sum(p.current_value or p.invested for p in rf_positions),
            "total_pnl": totais["pnl"] + sum(p.pnl or 0.0 for p in rf_positions),
            "total_pnl_pct": totais["pnl_pct"],
        }

    plano = strategy_service.generate_strategy(
        cash_available=cash,
        current_portfolio=current_portfolio,
        goals=goals,
        opportunities=opps_resp.items,
        portfolio_evaluation=portfolio_evaluation,
    )
    return affirmation.apply(plano)


@router.get("/rebalance-suggestions", dependencies=[Depends(requires(Feature.STRATEGY, cost=0))])
async def get_rebalance_suggestions() -> dict:
    stored = portfolio_repo.list_positions()
    current_portfolio = [
        PortfolioItem(
            ticker=i["ticker"],
            quantity=i["quantity"],
            avg_price=i["avg_price"],
            category=i.get("category", "auto"),
        )
        for i in stored
    ]
    rf_positions = _renda_fixa_como_posicoes()
    if not current_portfolio and not rf_positions:
        return affirmation.apply({"allocation_gaps": [], "items": [], "tax_disclaimer": None})

    goals = goal_service.get_goals()
    prefs = portfolio_repo.get_preferences()
    excluded_tickers = {t.upper() for t in prefs.get("excluded_tickers", [])}

    opps_resp = await opportunity_service.get_opportunities(
        include_held=False,
        page=1,
        page_size=50,
        sort_by="score",
        sort_order="desc",
    )

    posicoes = []
    if stored:
        eval_resp = await portfolio_service.evaluate_stored_for_current_user()
        posicoes = [p.model_dump() for p in eval_resp.positions]
    posicoes += [p.model_dump() for p in rf_positions]
    portfolio_evaluation = {"positions": posicoes}

    sugestoes = strategy_service.generate_rebalance_suggestions(
        current_portfolio=current_portfolio,
        goals=goals,
        opportunities=opps_resp.items,
        portfolio_evaluation=portfolio_evaluation,
        excluded_tickers=excluded_tickers,
    )
    return affirmation.apply(sugestoes)
