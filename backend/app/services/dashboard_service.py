from app.analysis.portfolio_health import compute_portfolio_health
from app.models import (
    Alert,
    CategoryAllocation,
    DashboardResponse,
    DashboardSummary,
    Goal,
    Opportunity,
    PortfolioPosition,
    PortfolioSnapshot,
)
from app.repositories import PortfolioRepository

REBALANCE_THRESHOLD_PCT = 5.0

_ASSET_TYPE_TO_CATEGORY = {
    "br_stock": "acoes_br",
    "fii": "fiis",
    "bdr": "bdrs",
    "etf": "etfs",
}

_VALID_CATEGORIES = {"renda_fixa", "acoes_br", "bdrs", "fiis", "etfs"}

_CATEGORY_LABELS = {
    "renda_fixa": "Renda Fixa",
    "acoes_br": "Ações BR",
    "bdrs": "BDRs",
    "fiis": "FIIs",
    "etfs": "ETFs",
}


class DashboardService:
    def __init__(self):
        self.portfolio_repo = PortfolioRepository()

    def classify_alerts(
        self,
        positions: list[PortfolioPosition],
        top_buys: list[Opportunity],
        allocations: list[CategoryAllocation],
    ) -> list[Alert]:
        alerts: list[Alert] = []

        for p in positions:
            if p.verdict in ("SELL", "STRONG_SELL"):
                alerts.append(
                    Alert(
                        severity="critical" if p.verdict == "STRONG_SELL" else "warning",
                        kind="sell_target",
                        title=f"{p.ticker}: sinal de venda",
                        detail=f"{p.label}. Preço atual R$ {p.current_price or 0:.2f}, justo R$ {p.fair_price or 0:.2f}.",
                        ticker=p.ticker,
                    )
                )

        for o in top_buys[:5]:
            if (o.margin_of_safety or 0) >= 0.30:
                alerts.append(
                    Alert(
                        severity="info",
                        kind="opportunity",
                        title=f"{o.ticker}: oportunidade forte",
                        detail=f"Margem de segurança {(o.margin_of_safety or 0) * 100:.0f}%. {o.label}.",
                        ticker=o.ticker,
                    )
                )

        sector_totals: dict[str, float] = {}
        total = sum(p.current_value or p.invested for p in positions) or 1.0

        for p in positions:
            if p.sector:
                sector_totals[p.sector] = sector_totals.get(p.sector, 0.0) + (
                    p.current_value or p.invested
                )

        for sector, value in sector_totals.items():
            pct = value / total * 100
            if pct > 30:
                alerts.append(
                    Alert(
                        severity="warning",
                        kind="concentration",
                        title=f"Setor {sector} concentrado",
                        detail=f"{pct:.1f}% da carteira em um único setor. Considere diversificar.",
                    )
                )

        for a in allocations:
            if a.target_pct is None or a.delta_pct is None:
                continue
            if abs(a.delta_pct) >= REBALANCE_THRESHOLD_PCT:
                direction = "acima" if a.delta_pct > 0 else "abaixo"
                label = _CATEGORY_LABELS.get(a.category, a.category)
                alerts.append(
                    Alert(
                        severity="warning",
                        kind="rebalance",
                        title=f"{label}: {direction} da meta",
                        detail=(
                            f"Atual {a.current_pct:.1f}% vs meta {a.target_pct:.1f}% "
                            f"({a.delta_pct:+.1f}pp)."
                        ),
                    )
                )

        return alerts

    def calculate_category_allocations(
        self,
        positions: list[PortfolioPosition],
        goals: list[Goal],
    ) -> list[CategoryAllocation]:
        totals: dict[str, float] = {
            "renda_fixa": 0.0,
            "acoes_br": 0.0,
            "bdrs": 0.0,
            "fiis": 0.0,
            "etfs": 0.0,
        }

        for p in positions:
            cat = p.category_resolved
            if cat not in _VALID_CATEGORIES:
                cat = _ASSET_TYPE_TO_CATEGORY.get(p.asset_type.value, "acoes_br")
            totals[cat] = totals.get(cat, 0.0) + (p.current_value or p.invested)

        total = sum(totals.values()) or 1.0
        target_map = {g.category: g.target_pct for g in goals}

        result: list[CategoryAllocation] = []
        for cat, value in totals.items():
            pct = value / total * 100
            target = target_map.get(cat)
            delta_pct = (pct - target) if target is not None else None
            delta_value = ((pct - target) / 100 * total) if target is not None else None

            result.append(
                CategoryAllocation(
                    category=cat,
                    current_value=round(value, 2),
                    current_pct=round(pct, 2),
                    target_pct=target,
                    delta_pct=round(delta_pct, 2) if delta_pct is not None else None,
                    delta_value=round(delta_value, 2) if delta_value is not None else None,
                )
            )

        return result

    async def generate_dashboard(
        self,
        positions: list[PortfolioPosition],
        top_buys: list[Opportunity],
        goals: list[Goal],
    ) -> DashboardResponse:

        real_positions = [p for p in positions if not p.ticker.startswith("RF_")]
        rf_positions = [p for p in positions if p.ticker.startswith("RF_")]

        top_sells = sorted(
            [p for p in real_positions if p.verdict in ("SELL", "STRONG_SELL")],
            key=lambda x: 0 if x.verdict == "STRONG_SELL" else 1,
        )

        allocations = self.calculate_category_allocations(positions, goals)
        alerts = self.classify_alerts(real_positions, top_buys, allocations)

        total_inv = sum(p.invested for p in positions)
        total_cur = sum(p.current_value or p.invested for p in positions)
        total_pnl = total_cur - total_inv
        total_pnl_pct = (total_pnl / total_inv * 100) if total_inv > 0 else 0.0

        total_yearly_dividends = 0.0
        for p in real_positions:
            if p.dividend_yield and p.current_value:
                yearly_div = p.current_value * (p.dividend_yield / 100)
                total_yearly_dividends += yearly_div

        for p in rf_positions:
            if p.dividend_yield and (p.current_value or p.invested):
                rf_value = p.current_value or p.invested
                yearly_rf = rf_value * (p.dividend_yield / 100)
                total_yearly_dividends += yearly_rf

        monthly_dividends = total_yearly_dividends / 12
        portfolio_yield = (total_yearly_dividends / total_cur * 100) if total_cur > 0 else 0.0

        prefs = self.portfolio_repo.get_preferences()
        passive_income_goal = prefs.get("passive_income_goal")
        passive_income_progress = None
        if passive_income_goal and passive_income_goal > 0:
            passive_income_progress = monthly_dividends / passive_income_goal * 100

        snaps = self.portfolio_repo.list_snapshots(limit=90)

        real_positions_count = len([p for p in positions if not p.ticker.startswith("RF_")])
        health = compute_portfolio_health(positions, allocations)

        return DashboardResponse(
            summary=DashboardSummary(
                total_invested=round(total_inv, 2),
                total_current=round(total_cur, 2),
                total_pnl=round(total_pnl, 2),
                total_pnl_pct=round(total_pnl_pct, 2),
                monthly_dividends_estimate=round(monthly_dividends, 2),
                yearly_dividends_estimate=round(total_yearly_dividends, 2),
                portfolio_yield=round(portfolio_yield, 2) if portfolio_yield > 0 else None,
                passive_income_goal=passive_income_goal,
                passive_income_progress=round(passive_income_progress, 2)
                if passive_income_progress
                else None,
                positions_count=real_positions_count,
            ),
            positions=positions,
            top_buys=top_buys,
            top_sells=top_sells,
            alerts=alerts,
            allocations=allocations,
            snapshots=[PortfolioSnapshot(**s) for s in snaps],
            health=health,
            last_updated=self.portfolio_repo.last_updated(),
        )
