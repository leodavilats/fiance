"""Service para geração do dashboard."""

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

# Mapa de AssetType → nova categoria
_ASSET_TYPE_TO_CATEGORY = {
    "br_stock": "acoes_br",
    "fii": "fiis",
    "us_stock": "acoes_int",
    "crypto": "cripto",
}

_VALID_CATEGORIES = {"renda_fixa", "acoes_br", "acoes_int", "fiis", "cripto"}


class DashboardService:
    """Service para geração do dashboard."""

    def __init__(self):
        self.portfolio_repo = PortfolioRepository()

    def classify_alerts(
        self,
        positions: list[PortfolioPosition],
        top_buys: list[Opportunity],
        allocations: list[CategoryAllocation],
    ) -> list[Alert]:
        """Classifica alertas baseados em posições e oportunidades."""
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

        return alerts

    def calculate_category_allocations(
        self,
        positions: list[PortfolioPosition],
        cash: float,
        goals: list[Goal],
    ) -> list[CategoryAllocation]:
        """Calcula alocação por categoria usando as novas categorias."""
        totals: dict[str, float] = {
            "renda_fixa": 0.0,
            "acoes_br": 0.0,
            "acoes_int": 0.0,
            "fiis": 0.0,
            "cripto": 0.0,
        }

        for p in positions:
            # Primeiro tenta category_resolved, depois mapeia pelo asset_type
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
        cash: float,
    ) -> DashboardResponse:
        """Gera o dashboard completo."""
        top_sells = sorted(
            [p for p in positions if p.verdict in ("SELL", "STRONG_SELL")],
            key=lambda x: 0 if x.verdict == "STRONG_SELL" else 1,
        )

        allocations = self.calculate_category_allocations(positions, cash, goals)
        alerts = self.classify_alerts(positions, top_buys, allocations)

        total_inv = sum(p.invested for p in positions)
        total_cur = sum(p.current_value or p.invested for p in positions)
        total_pnl = total_cur - total_inv
        total_pnl_pct = (total_pnl / total_inv * 100) if total_inv > 0 else 0.0

        snaps = self.portfolio_repo.list_snapshots(limit=90)

        return DashboardResponse(
            summary=DashboardSummary(
                total_invested=round(total_inv, 2),
                total_current=round(total_cur, 2),
                total_pnl=round(total_pnl, 2),
                total_pnl_pct=round(total_pnl_pct, 2),
                cash_available=round(cash, 2),
                monthly_dividends_estimate=0.0,
                portfolio_yield=None,
                positions_count=len(positions),
            ),
            positions=positions,
            top_buys=top_buys,
            top_sells=top_sells,
            alerts=alerts,
            allocations=allocations,
            snapshots=[PortfolioSnapshot(**s) for s in snaps],
            last_updated=self.portfolio_repo.last_updated(),
        )
