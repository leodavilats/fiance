from app.analysis.classify import auto_category
from app.models.quick_invest import (
    QuickInvestAllocation,
    QuickInvestRequest,
    QuickInvestResponse,
)
from app.repositories import AssetRepository, PortfolioRepository
from app.services import GoalService, OpportunityService


class QuickInvestService:
    def __init__(self):
        self.portfolio_repo = PortfolioRepository()
        self.asset_repo = AssetRepository()
        self.goal_service = GoalService()
        self.opportunity_service = OpportunityService()

    async def quick_invest(self, req: QuickInvestRequest) -> QuickInvestResponse:

        stored = self.portfolio_repo.list_positions()
        category_values: dict[str, float] = {}
        total_portfolio = 0.0

        for item in stored:
            try:
                snap = await self.asset_repo.get_asset(item["ticker"])
            except Exception:
                snap = None
            if not snap or not snap.price:
                continue

            value = item["quantity"] * snap.price
            total_portfolio += value

            cat = auto_category(snap.asset_type, snap.dividend_yield)
            category_values[cat] = category_values.get(cat, 0) + value

        goals = self.goal_service.get_goals() if req.use_current_goals else []
        goal_map = {g.category: g.target_pct for g in goals}

        future_total = total_portfolio + req.cash_available

        category_gaps: dict[str, float] = {}

        for cat, target_pct in goal_map.items():
            current_value = category_values.get(cat, 0.0)

            target_value = future_total * (target_pct / 100)
            gap = target_value - current_value

            if gap > 0:
                category_gaps[cat] = gap

        if not category_gaps or not req.prioritize_rebalance:
            category_gaps = {
                "acoes_br": req.cash_available * 0.5,
                "fiis": req.cash_available * 0.25,
                "renda_fixa": req.cash_available * 0.25,
            }

        opps_response = await self.opportunity_service.get_opportunities(
            page=1,
            page_size=30,
            sort_by="score",
            sort_order="desc",
        )
        opportunities = opps_response.items

        allocations: list[QuickInvestAllocation] = []
        allocated_total = 0.0

        gap_sum = sum(category_gaps.values())
        if gap_sum > 0:
            category_budget = {
                cat: (gap / gap_sum) * req.cash_available for cat, gap in category_gaps.items()
            }
        else:
            category_budget = {}

        for category, budget in category_budget.items():
            if budget < req.min_order_value:
                continue

            cat_opps = [
                opp
                for opp in opportunities
                if auto_category(
                    opp.asset_type.value
                    if hasattr(opp.asset_type, "value")
                    else str(opp.asset_type),
                    opp.dividend_yield,
                )
                == category
            ]

            if not cat_opps:
                continue

            cat_opps = sorted(cat_opps, key=lambda x: x.score or 0, reverse=True)[:3]

            weights = [0.7, 0.2, 0.1]

            for idx, opp in enumerate(cat_opps):
                if idx >= len(weights):
                    break

                allocation_value = budget * weights[idx]

                if allocation_value < req.min_order_value:
                    continue

                try:
                    snap = await self.asset_repo.get_asset(opp.ticker)
                except Exception:
                    snap = None
                if not snap or not snap.price:
                    continue

                quantity = int(allocation_value / snap.price)

                if quantity == 0:
                    continue

                actual_investment = quantity * snap.price

                allocations.append(
                    QuickInvestAllocation(
                        ticker=opp.ticker,
                        name=snap.name,
                        category=category,
                        sector=snap.sector,
                        current_price=snap.price,
                        suggested_quantity=quantity,
                        suggested_investment=round(actual_investment, 2),
                        rationale=self._build_rationale(opp, category, goal_map),
                        score=opp.score,
                        dividend_yield=opp.dividend_yield,
                    )
                )

                allocated_total += actual_investment

        new_category_values = category_values.copy()
        for alloc in allocations:
            cat = alloc.category
            new_category_values[cat] = new_category_values.get(cat, 0) + alloc.suggested_investment

        new_total = sum(new_category_values.values())
        portfolio_balance = {
            cat: {
                "value": round(val, 2),
                "percentage": round((val / new_total * 100), 2) if new_total > 0 else 0,
                "target": goal_map.get(cat, 0),
            }
            for cat, val in new_category_values.items()
        }

        summary = self._build_summary(allocations, req.cash_available, allocated_total)

        return QuickInvestResponse(
            total_cash=req.cash_available,
            allocated_cash=round(allocated_total, 2),
            remaining_cash=round(req.cash_available - allocated_total, 2),
            allocations=allocations,
            portfolio_balance=portfolio_balance,
            summary=summary,
        )

    def _build_rationale(self, opp, category: str, goals: dict[str, float]) -> str:
        reasons = []

        if goals.get(category, 0) > 0:
            reasons.append(f"Rebalanceamento de {category}")

        if opp.score and opp.score >= 80:
            reasons.append("Score excelente")
        elif opp.score and opp.score >= 70:
            reasons.append("Score alto")

        if opp.dividend_yield and opp.dividend_yield >= 8:
            reasons.append(f"DY {opp.dividend_yield:.1f}%")

        if opp.margin_of_safety and opp.margin_of_safety >= 20:
            reasons.append(f"MS {opp.margin_of_safety:.0f}%")

        if not reasons:
            reasons.append("Oportunidade identificada")

        return " | ".join(reasons)

    def _build_summary(
        self, allocations: list[QuickInvestAllocation], cash: float, allocated: float
    ) -> str:
        n = len(allocations)

        if n == 0:
            return "Não foi possível encontrar oportunidades adequadas no momento."

        lines = [
            f"Estratégia Quick Invest: {n} ativos selecionados.",
            f"Utilizando {allocated / cash * 100:.1f}% do caixa disponível (R$ {allocated:.2f}).",
        ]

        cats = {a.category for a in allocations}
        lines.append(f"Categorias: {', '.join(cats)}.")

        return " ".join(lines)
