from fastapi import APIRouter

from app.models import DashboardResponse, PortfolioEvaluationRequest, PortfolioItem
from app.repositories import PortfolioRepository
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
portfolio_repo = PortfolioRepository()
goal_service = GoalService()
fixed_income_service = FixedIncomeService()


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard() -> DashboardResponse:
    stored = portfolio_repo.list_positions()
    positions = []

    if stored:
        req = PortfolioEvaluationRequest(
            items=[
                PortfolioItem(
                    ticker=i["ticker"],
                    quantity=i["quantity"],
                    avg_price=i["avg_price"],
                    category=i.get("category", "auto"),
                )
                for i in stored
            ],
        )
        evaluation = await portfolio_service.evaluate_portfolio(req)
        positions = evaluation.positions

    # Renda fixa entra marcada a mercado, junto das posições negociadas: é o
    # que faz patrimônio total, P&L e projeção de renda passiva pararem de
    # ignorar metade da carteira de um investidor conservador.
    positions = positions + fixed_income_service.as_portfolio_positions()

    opps_resp = await opportunity_service.get_opportunities(
        include_held=False, page=1, page_size=10, sort_by="score", sort_order="desc"
    )
    top_buys = opps_resp.items[:5]

    goals = goal_service.get_goals()

    return await dashboard_service.generate_dashboard(positions, top_buys, goals)
