"""Controller para estratégia de investimento."""

from fastapi import APIRouter

from app.models import Goal, PortfolioEvaluationRequest, PortfolioItem
from app.repositories import PortfolioRepository
from app.services import OpportunityService, PortfolioService, StrategyService

router = APIRouter()

strategy_service = StrategyService()
opportunity_service = OpportunityService()
portfolio_service = PortfolioService()
portfolio_repo = PortfolioRepository()


@router.get("/strategy")
async def get_investment_strategy() -> dict:
    """Gera uma estratégia de investimento personalizada."""
    prefs = portfolio_repo.get_preferences()
    cash = prefs["cash_available"]
    desired_yield = prefs["desired_yield"]

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

    goals_data = portfolio_repo.list_goals()
    if not goals_data:
        goals = [
            Goal(category="renda", target_pct=40),
            Goal(category="trade", target_pct=50),
            Goal(category="cripto", target_pct=5),
            Goal(category="caixa", target_pct=5),
        ]
    else:
        goals = [Goal(**g) for g in goals_data]

    opps_resp = await opportunity_service.get_opportunities(
        include_held=False, only_buy=True, page=1, page_size=50, sort_by="score", sort_order="desc"
    )

    portfolio_evaluation = None
    if stored:
        req = PortfolioEvaluationRequest(items=current_portfolio, desired_yield=desired_yield)
        eval_resp = await portfolio_service.evaluate_portfolio(req)
        portfolio_evaluation = {
            "positions": [p.dict() for p in eval_resp.positions],
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
