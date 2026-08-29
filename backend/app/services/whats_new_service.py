from __future__ import annotations

import time

from app.analysis.score_ruler import is_highlight
from app.models.enums import AssetType
from app.models.whats_new import WhatsNewItem, WhatsNewResponse
from app.repositories import PortfolioRepository
from app.services.fixed_income_service import FixedIncomeService
from app.services.opportunity_service import OpportunityService
from app.services.portfolio_service import PortfolioService

MAX_ITEMS = 5

_PATRIMONY_NOISE_PCT = 0.5

_ALLOCATION_THRESHOLD_PCT = 5.0


class WhatsNewService:
    def __init__(self):
        self.portfolio_repo = PortfolioRepository()
        self.portfolio_service = PortfolioService()
        self.opportunity_service = OpportunityService()
        self.fixed_income = FixedIncomeService()

    async def build(self) -> WhatsNewResponse:
        items: list[WhatsNewItem] = []

        snapshots = self.portfolio_repo.list_snapshots(limit=30)
        evaluation = await self.portfolio_service.evaluate_stored_for_current_user()
        fixed_income = self.fixed_income.list_positions()

        items += self._patrimony_item(snapshots)
        items += self._verdict_items(evaluation.positions)
        items += self._maturity_items(fixed_income)
        items += self._allocation_items(evaluation.positions, fixed_income)
        items += self._tax_item()
        items += await self._opportunity_items(evaluation.positions)

        since = snapshots[0]["captured_at"] if len(snapshots) >= 2 else None
        latest = snapshots[-1]["captured_at"] if snapshots else None
        days_since = round((latest - since) / 86400, 1) if (since and latest) else None

        if not items:
            items = [
                WhatsNewItem(
                    kind="empty",
                    severity="info",
                    title="Nada de novo por aqui",
                    detail=(
                        "Sua carteira não mudou de forma relevante desde a última visita. "
                        "Sem notícia é boa notícia para quem investe no longo prazo."
                    ),
                    action="market",
                    action_label="Ver oportunidades",
                )
            ]

        return WhatsNewResponse(
            items=items[:MAX_ITEMS],
            since=since,
            days_since=days_since,
            generated_at=time.time(),
        )

    def _patrimony_item(self, snapshots: list[dict]) -> list[WhatsNewItem]:
        if len(snapshots) < 2:
            return []

        first, last = snapshots[0], snapshots[-1]
        opening = first["total_current"]
        if opening <= 0:
            return []

        flow = last["total_invested"] - first["total_invested"]
        change_pct = ((last["total_current"] - flow) / opening - 1) * 100

        if abs(change_pct) < _PATRIMONY_NOISE_PCT:
            return []

        days = max(round((last["captured_at"] - first["captured_at"]) / 86400), 1)
        window = "hoje" if days <= 1 else f"nos últimos {days} dias"
        direction = "subiu" if change_pct > 0 else "caiu"

        detail = (
            f"Variação de {abs(change_pct):.1f}% {window}, já descontando aportes "
            f"de R$ {flow:,.2f}."
            if abs(flow) > 0.01
            else f"Variação de {abs(change_pct):.1f}% {window}."
        )

        return [
            WhatsNewItem(
                kind="patrimony",
                severity="positive" if change_pct > 0 else "warning",
                title=f"Sua carteira {direction} {abs(change_pct):.1f}%",
                detail=detail,
                action="analyze",
                action_label="Ver a carteira",
            )
        ]

    def _verdict_items(self, positions: list) -> list[WhatsNewItem]:
        to_review = [p for p in positions if p.verdict in ("SELL", "STRONG_SELL")]
        if not to_review:
            return []

        to_review.sort(key=lambda p: 0 if p.verdict == "STRONG_SELL" else 1)
        names = ", ".join(p.ticker for p in to_review[:3])
        extra = f" e outros {len(to_review) - 3}" if len(to_review) > 3 else ""

        return [
            WhatsNewItem(
                kind="verdict_change",
                severity="critical" if to_review[0].verdict == "STRONG_SELL" else "warning",
                title=(
                    f"{len(to_review)} posição com sinal de venda"
                    if len(to_review) == 1
                    else f"{len(to_review)} posições com sinal de venda"
                ),
                detail=f"{names}{extra} — o preço passou do preço justo estimado.",
                ticker=to_review[0].ticker if len(to_review) == 1 else None,
                action="rebalance",
                action_label="Ver sugestões de ajuste",
            )
        ]

    def _maturity_items(self, fixed_income) -> list[WhatsNewItem]:
        vencendo = [i for i in fixed_income.items if not i.oculto and i.vencimento_proximo]
        if not vencendo:
            return []

        vencendo.sort(key=lambda i: i.dias_para_vencimento or 0)
        primeiro = vencendo[0]

        if len(vencendo) == 1:
            title = f"{primeiro.nome} vence em {primeiro.dias_para_vencimento} dias"
            detail = (
                f"R$ {primeiro.valor_no_vencimento or primeiro.valor_atual:,.2f} vão "
                "voltar para o caixa — decida onde reaplicar antes disso."
            )
        else:
            title = f"{len(vencendo)} aplicações vencem nos próximos 30 dias"
            detail = (
                f"A primeira é {primeiro.nome}, em {primeiro.dias_para_vencimento} dias. "
                "Planeje a reaplicação para o dinheiro não ficar parado."
            )

        return [
            WhatsNewItem(
                kind="maturity",
                severity="warning",
                title=title,
                detail=detail,
                action="fixed_income",
                action_label="Ver renda fixa",
            )
        ]

    def _allocation_items(self, positions: list, fixed_income) -> list[WhatsNewItem]:
        from app.services.dashboard_service import DashboardService
        from app.services.goal_service import GoalService

        all_positions = list(positions) + [
            p
            for p in self.fixed_income.as_portfolio_positions()
            if p.asset_type == AssetType.renda_fixa
        ]
        if not all_positions:
            return []

        allocations = DashboardService().calculate_category_allocations(
            all_positions, GoalService().get_goals()
        )

        off_target = [
            a
            for a in allocations
            if a.delta_pct is not None and abs(a.delta_pct) >= _ALLOCATION_THRESHOLD_PCT
        ]
        if not off_target:
            return []

        worst = max(off_target, key=lambda a: abs(a.delta_pct or 0))
        from app.services.dashboard_service import _CATEGORY_LABELS

        label = _CATEGORY_LABELS.get(worst.category, worst.category)
        direction = "acima" if (worst.delta_pct or 0) > 0 else "abaixo"

        return [
            WhatsNewItem(
                kind="allocation",
                severity="warning",
                title=f"{label} está {abs(worst.delta_pct or 0):.0f} pontos {direction} da meta",
                detail=(
                    f"Atual {worst.current_pct:.0f}% contra meta de {worst.target_pct:.0f}%. "
                    f"São {len(off_target)} categoria(s) fora da faixa."
                ),
                action="rebalance",
                action_label="Rebalancear",
            )
        ]

    def _tax_item(self) -> list[WhatsNewItem]:
        trades = self.portfolio_repo.list_closed_trades()
        if not trades:
            return []

        losses = [t for t in trades if t["gross_profit"] < 0]
        if not losses:
            return []

        total_loss = abs(sum(t["gross_profit"] for t in losses))
        if total_loss < 1:
            return []

        return [
            WhatsNewItem(
                kind="tax",
                severity="info",
                title=f"R$ {total_loss:,.2f} de prejuízo disponível para compensar IR",
                detail=(
                    "A legislação permite abater esse prejuízo de ganhos futuros da mesma "
                    "categoria. O app já considera isso ao estimar o IR de novas vendas."
                ),
                action="analyze",
                action_label="Ver operações encerradas",
            )
        ]

    async def _opportunity_items(self, positions: list) -> list[WhatsNewItem]:
        scanned, _universe = await self.opportunity_service.scan_for_current_user()
        held = {p.ticker.upper() for p in positions}

        prefs = self.portfolio_repo.get_preferences()
        excluded = {t.upper() for t in prefs.get("excluded_tickers", [])}

        highlights = [
            o
            for o in scanned
            if o.ticker.upper() not in held
            and o.ticker.upper() not in excluded
            and is_highlight(o.verdict, o.score, o.dividend_yield)
        ]
        if not highlights:
            return []

        highlights.sort(key=lambda o: o.score, reverse=True)
        best = highlights[0]

        return [
            WhatsNewItem(
                kind="new_opportunity",
                severity="positive",
                title=f"{best.ticker} está entre os destaques de hoje",
                detail=(
                    f"Score {best.score:.0f}"
                    + (f", DY {best.dividend_yield:.1f}%" if best.dividend_yield else "")
                    + f". {len(highlights)} ativo(s) fora da sua carteira em destaque."
                ),
                ticker=best.ticker,
                action="market",
                action_label="Ver oportunidades",
            )
        ]
