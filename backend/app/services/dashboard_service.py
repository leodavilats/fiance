from app.analysis.portfolio_health import compute_portfolio_health
from app.analysis.sectors import translate_sector
from app.models import (
    Alert,
    CategoryAllocation,
    DashboardResponse,
    DashboardSummary,
    DataFreshness,
    Goal,
    Opportunity,
    PortfolioPosition,
    PortfolioSnapshot,
)
from app.models.enums import AssetType
from app.repositories import PortfolioRepository

REBALANCE_THRESHOLD_PCT = 5.0

SECTOR_CONCENTRATION_PCT = 30.0

MAX_ALERTS = 4

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

        alerts += self._sell_alert(positions)
        alerts += self._opportunity_alert(top_buys)
        alerts += self._concentration_alert(positions)
        alerts += self._rebalance_alert(allocations)

        severity_order = {"critical": 0, "warning": 1, "info": 2}
        alerts.sort(key=lambda a: severity_order.get(a.severity, 3))

        return alerts[:MAX_ALERTS]

    @staticmethod
    def _sell_alert(positions: list[PortfolioPosition]) -> list[Alert]:
        to_sell = [p for p in positions if p.verdict in ("SELL", "STRONG_SELL")]
        if not to_sell:
            return []

        to_sell.sort(key=lambda p: 0 if p.verdict == "STRONG_SELL" else 1)
        strong = [p for p in to_sell if p.verdict == "STRONG_SELL"]

        if len(to_sell) == 1:
            position = to_sell[0]
            return [
                Alert(
                    severity="critical" if strong else "warning",
                    kind="sell_target",
                    title=f"{position.ticker}: sinal de venda",
                    detail=(
                        f"{position.label}. Preço atual R$ {position.current_price or 0:.2f}, "
                        f"justo R$ {position.fair_price or 0:.2f}."
                    ),
                    ticker=position.ticker,
                    count=1,
                    tickers=[position.ticker],
                    action="sell",
                    action_label="Simular venda",
                )
            ]

        names = ", ".join(p.ticker for p in to_sell[:4])
        extra = f" e outros {len(to_sell) - 4}" if len(to_sell) > 4 else ""
        return [
            Alert(
                severity="critical" if strong else "warning",
                kind="sell_target",
                title=f"{len(to_sell)} posições com sinal de venda",
                detail=f"{names}{extra} — o preço passou do preço justo estimado.",
                count=len(to_sell),
                tickers=[p.ticker for p in to_sell],
                action="rebalance",
                action_label="Ver sugestões de ajuste",
            )
        ]

    @staticmethod
    def _opportunity_alert(top_buys: list[Opportunity]) -> list[Alert]:
        strong = [o for o in top_buys[:5] if (o.margin_of_safety or 0) >= 0.30]
        if not strong:
            return []

        best = strong[0]
        if len(strong) == 1:
            detail = f"Margem de segurança {(best.margin_of_safety or 0) * 100:.0f}%. {best.label}."
            title = f"{best.ticker}: oportunidade forte"
        else:
            names = ", ".join(o.ticker for o in strong)
            title = f"{len(strong)} oportunidades com desconto acima de 30%"
            detail = f"{names}. A maior margem é de {best.ticker}."

        return [
            Alert(
                severity="info",
                kind="opportunity",
                title=title,
                detail=detail,
                ticker=best.ticker if len(strong) == 1 else None,
                count=len(strong),
                tickers=[o.ticker for o in strong],
                action="analyze",
                action_label="Ver análise",
            )
        ]

    @staticmethod
    def _concentration_alert(positions: list[PortfolioPosition]) -> list[Alert]:
        total = sum(p.current_value or p.invested for p in positions) or 1.0

        sector_totals: dict[str, float] = {}
        for p in positions:
            if p.sector:
                sector_totals[p.sector] = sector_totals.get(p.sector, 0.0) + (
                    p.current_value or p.invested
                )

        concentrated = [
            (sector, value / total * 100)
            for sector, value in sector_totals.items()
            if value / total * 100 > SECTOR_CONCENTRATION_PCT
        ]
        if not concentrated:
            return []

        concentrated.sort(key=lambda item: -item[1])
        worst_sector, worst_pct = concentrated[0]
        label = translate_sector(worst_sector)

        if len(concentrated) == 1:
            title = f"Setor {label} concentrado"
            detail = f"{worst_pct:.1f}% da carteira em um único setor. Considere diversificar."
        else:
            title = f"{len(concentrated)} setores concentrados"
            detail = f"O maior é {label}, com {worst_pct:.1f}% da carteira. Considere diversificar."

        return [
            Alert(
                severity="warning",
                kind="concentration",
                title=title,
                detail=detail,
                count=len(concentrated),
                action="rebalance",
                action_label="Rebalancear",
            )
        ]

    @staticmethod
    def _rebalance_alert(allocations: list[CategoryAllocation]) -> list[Alert]:
        off_target = [
            a
            for a in allocations
            if a.target_pct is not None
            and a.delta_pct is not None
            and abs(a.delta_pct) >= REBALANCE_THRESHOLD_PCT
        ]
        if not off_target:
            return []

        off_target.sort(key=lambda a: -abs(a.delta_pct or 0))
        worst = off_target[0]
        label = _CATEGORY_LABELS.get(worst.category, worst.category)
        direction = "acima" if (worst.delta_pct or 0) > 0 else "abaixo"

        if len(off_target) == 1:
            title = f"{label}: {direction} da meta"
            detail = (
                f"Atual {worst.current_pct:.1f}% vs meta {worst.target_pct:.1f}% "
                f"({worst.delta_pct:+.1f}pp)."
            )
        else:
            title = f"{len(off_target)} categorias fora da meta"
            detail = (
                f"A maior diferença é {label}: {worst.current_pct:.1f}% contra meta de "
                f"{worst.target_pct:.1f}% ({worst.delta_pct:+.1f}pp)."
            )

        return [
            Alert(
                severity="warning",
                kind="rebalance",
                title=title,
                detail=detail,
                count=len(off_target),
                action="goals",
                action_label="Ajustar meta",
            )
        ]

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
        freshness: DataFreshness | None = None,
        dividends_received_this_month: float = 0.0,
        dividends_received_last_12m: float = 0.0,
    ) -> DashboardResponse:

        real_positions = [p for p in positions if p.asset_type != AssetType.renda_fixa]
        rf_positions = [p for p in positions if p.asset_type == AssetType.renda_fixa]

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

        real_positions_count = len(real_positions)
        health = compute_portfolio_health(positions, allocations)

        return DashboardResponse(
            summary=DashboardSummary(
                total_invested=round(total_inv, 2),
                total_current=round(total_cur, 2),
                total_pnl=round(total_pnl, 2),
                total_pnl_pct=round(total_pnl_pct, 2),
                monthly_dividends_estimate=round(monthly_dividends, 2),
                yearly_dividends_estimate=round(total_yearly_dividends, 2),
                dividends_received_this_month=dividends_received_this_month,
                dividends_received_last_12m=dividends_received_last_12m,
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
            freshness=freshness,
            last_updated=self.portfolio_repo.last_updated(),
        )
