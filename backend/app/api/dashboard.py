from fastapi import APIRouter

from app.models import DashboardResponse, PortfolioEvaluationRequest, PortfolioItem
from app.repositories import PortfolioRepository
from app.services import DashboardService, OpportunityService, PortfolioService

router = APIRouter()

dashboard_service = DashboardService()
opportunity_service = OpportunityService()
portfolio_service = PortfolioService()
portfolio_repo = PortfolioRepository()


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard() -> DashboardResponse:
    prefs = portfolio_repo.get_preferences()
    cash = prefs["cash_available"]
    desired_yield = prefs["desired_yield"]

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
            desired_yield=desired_yield,
        )
        evaluation = await portfolio_service.evaluate_portfolio(req)
        positions = evaluation.positions

    opps_resp = await opportunity_service.get_opportunities(
        include_held=False, page=1, page_size=10, sort_by="score", sort_order="desc"
    )
    top_buys = opps_resp.items[:5]

    goals_data = portfolio_repo.list_goals()
    if not goals_data:
        from app.models import Goal

        goals = [
            Goal(category="renda", target_pct=40),
            Goal(category="trade", target_pct=50),
            Goal(category="cripto", target_pct=5),
            Goal(category="caixa", target_pct=5),
        ]
    else:
        from app.models import Goal

        goals = [Goal(**g) for g in goals_data]

    return await dashboard_service.generate_dashboard(positions, top_buys, goals, cash)
