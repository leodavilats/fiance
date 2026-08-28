from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import date

from app.collectors.universal import fetch_ibov_history
from app.core.brt import now_brt
from app.core.errors import NotFoundError
from app.core.pagination import clamp_limit, slice_after
from app.models.followed import (
    FollowedSuggestion,
    FollowedSuggestionCreate,
    FollowedSuggestionsResponse,
    SuggestionOutcomeGroup,
)
from app.repositories import AssetRepository
from app.storage import portfolio_store

_SOURCE_LABELS = {
    "opportunities": "Oportunidades",
    "rebalance": "Sugestões de ajuste",
    "quick_invest": "Quick Invest",
    "strategy": "Estratégia",
    "dip_scanner": "Scanner de quedas",
    "whats_new": "O que mudou",
}


class FollowedService:
    """Resultado das sugestões que o usuário seguiu."""

    def __init__(self):
        self.asset_repo = AssetRepository()

    def register(self, req: FollowedSuggestionCreate) -> FollowedSuggestion:
        row = portfolio_store.create_followed_suggestion(
            ticker=req.ticker.upper(),
            source=req.source,
            action=req.action,
            quantity=req.quantity,
            price=req.price,
            followed_on=(req.followed_on or now_brt().date()).isoformat(),
            score_at_suggestion=req.score_at_suggestion,
            verdict_at_suggestion=req.verdict_at_suggestion,
            note=req.note,
        )
        return FollowedSuggestion(
            **{**row, "followed_on": date.fromisoformat(row["followed_on"])},
            invested=round(row["quantity"] * row["price"], 2),
        )

    def delete(self, suggestion_id: int) -> dict:
        if not portfolio_store.delete_followed_suggestion(suggestion_id):
            raise NotFoundError(f"Sugestão seguida {suggestion_id} não encontrada.")
        return {"deleted": suggestion_id}

    async def outcomes(
        self, limit: int | None = None, cursor: str | None = None
    ) -> FollowedSuggestionsResponse:
        """Resultado das sugestões seguidas, com totais sobre o conjunto inteiro.

        A comparação contra o Ibovespa e o agrupamento por origem precisam de
        todas as sugestões, então a paginação limita o payload e não a consulta.
        """
        rows = portfolio_store.list_followed_suggestions()
        if not rows:
            return FollowedSuggestionsResponse(
                summary=(
                    "Nenhuma sugestão marcada como seguida ainda. Ao registrar as que você "
                    "executar, esta tela mostra o resultado — e você pode auditar o produto."
                )
            )

        tickers = sorted({row["ticker"] for row in rows})
        prices, ibov = await asyncio.gather(
            self._current_prices(tickers),
            fetch_ibov_history(days=400),
        )

        today = now_brt().date()
        items: list[FollowedSuggestion] = []

        for row in rows:
            followed_on = date.fromisoformat(row["followed_on"])
            invested = row["quantity"] * row["price"]
            price_now = prices.get(row["ticker"])

            current_value = row["quantity"] * price_now if price_now else None
            pnl = (current_value - invested) if current_value is not None else None
            pnl_pct = (pnl / invested * 100) if (pnl is not None and invested > 0) else None

            ibov_pct = self._ibov_change(ibov, followed_on)

            items.append(
                FollowedSuggestion(
                    id=row["id"],
                    ticker=row["ticker"],
                    source=row["source"],
                    action=row["action"],
                    quantity=row["quantity"],
                    price=row["price"],
                    followed_on=followed_on,
                    score_at_suggestion=row["score_at_suggestion"],
                    verdict_at_suggestion=row["verdict_at_suggestion"],
                    note=row["note"],
                    invested=round(invested, 2),
                    current_value=round(current_value, 2) if current_value is not None else None,
                    pnl=round(pnl, 2) if pnl is not None else None,
                    pnl_pct=round(pnl_pct, 2) if pnl_pct is not None else None,
                    days_held=(today - followed_on).days,
                    ibov_pct_since=ibov_pct,
                    beat_ibov=(pnl_pct > ibov_pct)
                    if (pnl_pct is not None and ibov_pct is not None)
                    else None,
                )
            )

        priced = [i for i in items if i.current_value is not None]
        total_invested = sum(i.invested for i in priced)
        total_current = sum(i.current_value or 0 for i in priced)
        total_pnl = total_current - total_invested
        total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0

        oldest = min((i.followed_on for i in items), default=None)
        ibov_pct = self._ibov_change(ibov, oldest) if oldest else None

        by_source = self._group_by_source(priced, ibov)
        page = slice_after(
            items,
            cursor,
            clamp_limit(limit),
            key=lambda i: str(i.followed_on),
            identity=lambda i: i.id,
        )

        return FollowedSuggestionsResponse(
            items=page.items,
            next_cursor=page.next_cursor,
            has_more=page.has_more,
            total_count=len(items),
            total_invested=round(total_invested, 2),
            total_current_value=round(total_current, 2),
            total_pnl=round(total_pnl, 2),
            total_pnl_pct=round(total_pnl_pct, 2),
            ibov_pct_same_period=ibov_pct,
            beat_ibov=(total_pnl_pct > ibov_pct) if ibov_pct is not None else None,
            by_source=by_source,
            summary=self._summary(len(priced), total_pnl_pct, ibov_pct),
        )

    async def _current_prices(self, tickers: list[str]) -> dict[str, float]:
        async def _one(ticker: str):
            try:
                return ticker, await self.asset_repo.get_asset(ticker)
            except Exception:
                return ticker, None

        results = await asyncio.gather(*[_one(t) for t in tickers])
        return {ticker: snap.price for ticker, snap in results if snap is not None and snap.price}

    @staticmethod
    def _ibov_change(series: dict[str, float], since: date | None) -> float | None:
        if not series or since is None:
            return None

        target = since.isoformat()
        base = next((v for day, v in sorted(series.items()) if day >= target), None)
        last = series[max(series)] if series else None

        if not base or not last or base <= 0:
            return None
        return round((last / base - 1) * 100, 2)

    def _group_by_source(
        self, items: list[FollowedSuggestion], ibov: dict[str, float]
    ) -> list[SuggestionOutcomeGroup]:
        buckets: dict[str, list[FollowedSuggestion]] = defaultdict(list)
        for item in items:
            buckets[item.source].append(item)

        groups: list[SuggestionOutcomeGroup] = []
        for source, group in buckets.items():
            invested = sum(i.invested for i in group)
            current = sum(i.current_value or 0 for i in group)
            pnl = current - invested
            oldest = min(i.followed_on for i in group)

            groups.append(
                SuggestionOutcomeGroup(
                    source=_SOURCE_LABELS.get(source, source),
                    count=len(group),
                    invested=round(invested, 2),
                    current_value=round(current, 2),
                    pnl=round(pnl, 2),
                    pnl_pct=round(pnl / invested * 100, 2) if invested > 0 else 0.0,
                    ibov_pct=self._ibov_change(ibov, oldest),
                )
            )

        groups.sort(key=lambda g: -g.pnl_pct)
        return groups

    @staticmethod
    def _summary(count: int, pnl_pct: float, ibov_pct: float | None) -> str:
        if count == 0:
            return (
                "As sugestões registradas ainda não têm cotação disponível para apurar o resultado."
            )

        plural = "compra" if count == 1 else "compras"
        base = f"As {count} {plural} que você fez a partir de sugestões estão {pnl_pct:+.1f}%"

        if ibov_pct is None:
            return base + "."

        comparison = "acima" if pnl_pct > ibov_pct else "abaixo"
        return f"{base} contra {ibov_pct:+.1f}% do Ibovespa no período — {comparison} do índice."
