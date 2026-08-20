from fastapi import APIRouter

from app.models import PortfolioItem
from app.repositories import PortfolioRepository
from app.services import GoalService, OpportunityService, PortfolioService, StrategyService

router = APIRouter()

strategy_service = StrategyService()
opportunity_service = OpportunityService()
portfolio_service = PortfolioService()
portfolio_repo = PortfolioRepository()
goal_service = GoalService()


@router.get("/strategy")
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

    goals = goal_service.get_goals()

    opps_resp = await opportunity_service.get_opportunities(
        include_held=False,
        page=1,
        page_size=50,
        sort_by="score",
        sort_order="desc",
    )

    portfolio_evaluation = None
    if stored:
        eval_resp = await portfolio_service.evaluate_stored_for_current_user()
        portfolio_evaluation = {
            "positions": [p.model_dump() for p in eval_resp.positions],
            "total_invested": eval_resp.total_invested,
            "total_current": eval_resp.total_current,
            "total_pnl": eval_resp.total_pnl,
            "total_pnl_pct": eval_resp.total_pnl_pct,
        }

    return strategy_service.generate_strategy(
        cash_available=cash,
        current_portfolio=current_portfolio,
        goals=goals,
        opportunities=opps_resp.items,
        portfolio_evaluation=portfolio_evaluation,
    )


@router.get("/rebalance-suggestions")
async def get_rebalance_suggestions() -> dict:
    stored = portfolio_repo.list_positions()
    if not stored:
        return {"allocation_gaps": [], "items": [], "tax_disclaimer": None}

    current_portfolio = [
        PortfolioItem(
            ticker=i["ticker"],
            quantity=i["quantity"],
            avg_price=i["avg_price"],
            category=i.get("category", "auto"),
        )
        for i in stored
    ]

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

    eval_resp = await portfolio_service.evaluate_stored_for_current_user()
    portfolio_evaluation = {"positions": [p.model_dump() for p in eval_resp.positions]}

    return strategy_service.generate_rebalance_suggestions(
        current_portfolio=current_portfolio,
        goals=goals,
        opportunities=opps_resp.items,
        portfolio_evaluation=portfolio_evaluation,
        excluded_tickers=excluded_tickers,
    )
