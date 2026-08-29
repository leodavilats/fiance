from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from app.core.money import money, quantize
from app.ledger import project_position
from app.repositories import AssetRepository, PortfolioRepository
from app.storage import ledger_store

logger = logging.getLogger("fiance.dividend_calendar")

LOOKBACK_DAYS = 400

JCP_WITHHOLDING_PCT = 15.0

_JCP_HINTS = ("jcp", "juros sobre capital", "juros s/ capital")


@dataclass
class DividendSuggestion:
    ticker: str
    paid_at: str
    quantity_at_date: float
    rate_per_share: float
    amount: float
    kind: str
    caveats: list[str] = field(default_factory=list)
    quantity_is_current: bool = False

    def as_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "paid_at": self.paid_at,
            "quantity_at_date": self.quantity_at_date,
            "rate_per_share": self.rate_per_share,
            "amount": self.amount,
            "kind": self.kind,
            "caveats": list(self.caveats),
            "quantity_is_current": self.quantity_is_current,
        }


def _classify(raw: dict) -> str:
    label = str(raw.get("label") or raw.get("type") or "").lower()
    if any(hint in label for hint in _JCP_HINTS):
        return "jcp"
    return "dividendo"


class DividendCalendarService:
    def __init__(self):
        self.asset_repo = AssetRepository()
        self.portfolio_repo = PortfolioRepository()

    async def pending(self, user_id: str | None = None) -> dict:
        posicoes = self.portfolio_repo.list_positions()
        if not posicoes:
            return {"items": [], "note": "Sem posições na carteira — nada a sugerir."}

        ja_lancados = {
            (row["ticker"], str(row["paid_at"]))
            for row in self.portfolio_repo.list_dividends_received()
        }

        cutoff = self._cutoff()
        lancamentos = self._entries_by_symbol(user_id)

        resultados = await asyncio.gather(
            *(self._for_ticker(p, ja_lancados, cutoff, lancamentos) for p in posicoes),
            return_exceptions=True,
        )

        items: list[DividendSuggestion] = []
        for posicao, resultado in zip(posicoes, resultados, strict=True):
            if isinstance(resultado, list):
                items.extend(resultado)
            elif isinstance(resultado, Exception):
                logger.warning(
                    "Calendário de proventos falhou para %s: %s", posicao["ticker"], resultado
                )

        items.sort(key=lambda s: (s.paid_at, s.ticker), reverse=True)

        return {
            "items": [s.as_dict() for s in items],
            "count": len(items),
            "note": (
                "Sugestões do calendário da fonte cruzadas com a sua carteira. Nada foi "
                "lançado: confira contra o extrato da corretora antes de confirmar."
            ),
        }

    @staticmethod
    def _cutoff() -> str:
        from datetime import timedelta

        from app.core.brt import now_brt

        return (now_brt().date() - timedelta(days=LOOKBACK_DAYS)).isoformat()

    @staticmethod
    def _entries_by_symbol(user_id: str | None) -> dict[str, list]:
        agrupados: dict[str, list] = {}
        for entry in ledger_store.list_entries(user_id=user_id):
            agrupados.setdefault(entry.symbol.strip().upper(), []).append(entry)
        return agrupados

    async def _for_ticker(
        self,
        posicao: dict,
        ja_lancados: set[tuple[str, str]],
        cutoff: str,
        lancamentos: dict[str, list],
    ) -> list[DividendSuggestion]:
        ticker = posicao["ticker"].upper()
        calendario = await self.asset_repo.get_dividends(ticker)
        if not calendario:
            return []

        do_ativo = lancamentos.get(ticker, [])
        sugestoes: list[DividendSuggestion] = []

        for pago in calendario:
            dia = str(pago.get("date") or "")[:10]
            taxa = pago.get("value")

            if not dia or dia < cutoff or not taxa or taxa <= 0:
                continue
            if (ticker, dia) in ja_lancados:
                continue

            quantidade, do_razao = self._quantity_at(do_ativo, dia, posicao)
            if quantidade <= 0:
                continue

            kind = _classify(pago)
            caveats = [
                "A fonte publica a data de pagamento, não a data-com. Se você comprou "
                "entre uma e outra, este provento não é seu."
            ]
            if not do_razao:
                caveats.append(
                    "Quantidade estimada pela posição de hoje: o livro-razão não tem "
                    "lançamentos deste ativo antes desta data."
                )
            if kind == "jcp":
                caveats.append(
                    f"JCP tem {JCP_WITHHOLDING_PCT:.0f}% de IR retido na fonte. O valor "
                    "abaixo é bruto."
                )

            sugestoes.append(
                DividendSuggestion(
                    ticker=ticker,
                    paid_at=dia,
                    quantity_at_date=quantidade,
                    rate_per_share=float(taxa),
                    amount=float(quantize(money(quantidade) * money(taxa))),
                    kind=kind,
                    caveats=caveats,
                    quantity_is_current=not do_razao,
                )
            )

        return sugestoes

    @staticmethod
    def _quantity_at(entries: list, day: str, posicao: dict) -> tuple[float, bool]:
        anteriores = [e for e in entries if e.traded_on <= day]
        if not anteriores:
            return float(posicao["quantity"]), False

        return float(project_position(anteriores).quantity), True
