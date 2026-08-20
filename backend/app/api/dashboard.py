from fastapi import APIRouter

from app.collectors.rates import get_rates
from app.collectors.universal import FUND_TTL
from app.models import DashboardResponse, DataFreshness
from app.services import (
    DashboardService,
    FixedIncomeService,
    GoalService,
    OpportunityService,
    PortfolioService,
)

router = APIRouter()

dashboard_service = DashboardService()
opportunity_service = OpportunityService()
portfolio_service = PortfolioService()
goal_service = GoalService()
fixed_income_service = FixedIncomeService()


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard() -> DashboardResponse:
    evaluation = await portfolio_service.evaluate_stored_for_current_user()

    # Renda fixa entra marcada a mercado, junto das posições negociadas: é o
    # que faz patrimônio total, P&L e projeção de renda passiva pararem de
    # ignorar metade da carteira de um investidor conservador.
    positions = list(evaluation.positions) + fixed_income_service.as_portfolio_positions()

    opps_resp = await opportunity_service.get_opportunities(
        include_held=False, page=1, page_size=10, sort_by="score", sort_order="desc"
    )
    top_buys = opps_resp.items[:5]

    goals = goal_service.get_goals()

    age = await opportunity_service.market_data_age_seconds()
    freshness = DataFreshness(
        rates_source=get_rates()["source"],
        market_data_age_seconds=round(age, 1) if age is not None else None,
        market_data_stale=age is not None and age > FUND_TTL,
        quotes_ttl_seconds=FUND_TTL,
    )

    return await dashboard_service.generate_dashboard(positions, top_buys, goals, freshness)
