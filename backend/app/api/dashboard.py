import asyncio

from fastapi import APIRouter

from app.collectors.rates import get_rates
from app.collectors.universal import pregao_da_base, validade
from app.core.pregao import ultimo_pregao_carregado
from app.models import DashboardResponse, DataFreshness
from app.services import (
    DashboardService,
    DividendsService,
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
dividends_service = DividendsService()


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard() -> DashboardResponse:
    evaluation = await portfolio_service.evaluate_stored_for_current_user()

    positions = list(evaluation.positions) + fixed_income_service.as_portfolio_positions()

    opps_resp = await opportunity_service.get_opportunities(
        include_held=False, page=1, page_size=10, sort_by="score", sort_order="desc"
    )
    top_buys = opps_resp.items[:5]

    goals = goal_service.goals_for_judgement()

    age = await opportunity_service.market_data_age_seconds()
    pregao = await asyncio.to_thread(pregao_da_base)
    freshness = DataFreshness(
        rates_source=get_rates()["source"],
        market_data_age_seconds=round(age, 1) if age is not None else None,
        market_data_stale=pregao is not None and pregao < ultimo_pregao_carregado(),
        quotes_ttl_seconds=validade(pregao),
    )

    received = dividends_service.list_received()

    return await dashboard_service.generate_dashboard(
        positions,
        top_buys,
        goals,
        freshness,
        dividends_received_this_month=received.received_this_month,
        dividends_received_last_12m=received.received_last_12m,
    )
