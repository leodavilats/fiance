from app.models import (
    PortfolioEvaluationRequest,
    PortfolioItem,
    QuickInvestRequest,
    RebalanceResponse,
)
from app.repositories import PortfolioRepository
from app.services.dashboard_service import REBALANCE_THRESHOLD_PCT, DashboardService
from app.services.goal_service import GoalService
from app.services.portfolio_service import PortfolioService
from app.services.quick_invest_service import QuickInvestService

MIN_GAP_TO_SUGGEST = 100.0


class RebalanceService:
    def __init__(self):
        self.portfolio_repo = PortfolioRepository()
        self.portfolio_service = PortfolioService()
        self.goal_service = GoalService()
        self.dashboard_service = DashboardService()
        self.quick_invest_service = QuickInvestService()

    async def get_rebalance_plan(self) -> RebalanceResponse:
        stored = self.portfolio_repo.list_positions()
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
            evaluation = await self.portfolio_service.evaluate_portfolio(req)
            positions = evaluation.positions

        goals = self.goal_service.get_goals()
        allocations = self.dashboard_service.calculate_category_allocations(positions, goals)

        needs_rebalance = any(
            a.target_pct is not None
            and a.delta_pct is not None
            and abs(a.delta_pct) >= REBALANCE_THRESHOLD_PCT
            for a in allocations
        )

        total_gap = sum(
            -a.delta_value for a in allocations if a.delta_value is not None and a.delta_value < 0
        )

        if not needs_rebalance or total_gap < MIN_GAP_TO_SUGGEST:
            message = (
                "Sua carteira está alinhada com as metas de alocação."
                if not needs_rebalance
                else "Desvio pequeno demais para sugerir ordens de compra específicas."
            )
            return RebalanceResponse(
                needs_rebalance=needs_rebalance,
                allocations=allocations,
                total_gap_amount=round(total_gap, 2),
                suggestions=[],
                message=message,
            )

        quick_invest_result = await self.quick_invest_service.quick_invest(
            QuickInvestRequest(
                cash_available=total_gap,
                use_current_goals=True,
                prioritize_rebalance=True,
                min_order_value=100.0,
            )
        )

        return RebalanceResponse(
            needs_rebalance=True,
            allocations=allocations,
            total_gap_amount=round(total_gap, 2),
            suggestions=quick_invest_result.allocations,
            message=(
                f"Faltam R$ {total_gap:.2f} para alinhar sua carteira às metas. "
                f"Veja as sugestões de compra abaixo."
            ),
        )
