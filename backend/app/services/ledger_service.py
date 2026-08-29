from __future__ import annotations

import logging

from app.core.brt import now_brt
from app.ledger import LedgerEntry, TransactionKind, explain_position, project_positions
from app.ledger.projection import PositionProjection
from app.storage import audit_store, ledger_store, portfolio_store

logger = logging.getLogger("fiance.ledger")

QUANTITY_TOLERANCE = 1e-6
PRICE_TOLERANCE = 1e-4


def today_brt() -> str:
    return now_brt().strftime("%Y-%m-%d")


def mirror_position_state(
    ticker: str,
    quantity: float,
    avg_price: float,
    traded_on: str | None = None,
    user_id: str | None = None,
) -> None:
    try:
        ledger_store.record(
            LedgerEntry(
                kind=TransactionKind.ADJUST,
                symbol=ticker,
                traded_on=traded_on or today_brt(),
                quantity=quantity,
                price=avg_price,
            ),
            source="position_editor",
            user_id=user_id,
        )
    except Exception:
        logger.warning("Falha ao espelhar posição %s no razão", ticker, exc_info=True)


def mirror_sale(
    ticker: str,
    quantity: float,
    price: float,
    fees: float = 0.0,
    traded_on: str | None = None,
    user_id: str | None = None,
) -> None:
    try:
        ledger_store.record(
            LedgerEntry(
                kind=TransactionKind.SELL,
                symbol=ticker,
                traded_on=traded_on or today_brt(),
                quantity=quantity,
                price=price,
                fees=max(0.0, fees),
            ),
            source="sell",
            user_id=user_id,
        )
    except Exception:
        logger.warning("Falha ao espelhar venda de %s no razão", ticker, exc_info=True)


def mirror_removal(ticker: str, user_id: str | None = None) -> None:
    try:
        ledger_store.record(
            LedgerEntry(
                kind=TransactionKind.ADJUST,
                symbol=ticker,
                traded_on=today_brt(),
                quantity=0.0,
                price=0.0,
            ),
            source="position_editor",
            user_id=user_id,
        )
    except Exception:
        logger.warning("Falha ao espelhar remoção de %s no razão", ticker, exc_info=True)


def project(user_id: str | None = None) -> dict[str, PositionProjection]:
    return project_positions(ledger_store.list_entries(user_id=user_id))


def reconcile(user_id: str | None = None) -> dict:
    stored = {item["ticker"]: item for item in portfolio_store.list_positions(user_id)}
    projected = {symbol: state for symbol, state in project(user_id).items() if state.is_open}

    differences: list[dict] = []

    for ticker in sorted(set(stored) | set(projected)):
        current = stored.get(ticker)
        derived = projected.get(ticker)

        if current is None:
            differences.append(
                {
                    "ticker": ticker,
                    "reason": "no_razao_sem_posicao",
                    "stored": None,
                    "projected": derived.as_dict(),
                }
            )
            continue

        if derived is None:
            differences.append(
                {
                    "ticker": ticker,
                    "reason": "posicao_sem_razao",
                    "stored": current,
                    "projected": None,
                }
            )
            continue

        quantity_off = abs(current["quantity"] - derived.quantity) > QUANTITY_TOLERANCE
        price_off = abs(current["avg_price"] - derived.avg_price) > PRICE_TOLERANCE

        if quantity_off or price_off:
            differences.append(
                {
                    "ticker": ticker,
                    "reason": "quantidade" if quantity_off else "preco_medio",
                    "stored": current,
                    "projected": derived.as_dict(),
                }
            )

    return {
        "positions": len(stored),
        "projected": len(projected),
        "differences": differences,
        "in_sync": not differences,
    }


def backfill_from_positions(user_id: str | None = None) -> int:
    existing = set(ledger_store.symbols(user_id=user_id))
    entries = [
        LedgerEntry(
            kind=TransactionKind.ADJUST,
            symbol=item["ticker"],
            traded_on=today_brt(),
            quantity=item["quantity"],
            price=item["avg_price"],
            note="Estado importado da carteira anterior ao livro-razão.",
        )
        for item in portfolio_store.list_positions(user_id)
        if item["ticker"] not in existing
    ]

    if not entries:
        return 0

    ledger_store.record_many(entries, source="backfill", user_id=user_id)
    audit_store.write(
        audit_store.LEDGER_WRITE,
        entity="ledger",
        summary=f"{len(entries)} posição(ões) semeadas no livro-razão.",
        detail={"symbols": [e.symbol for e in entries]},
        user_id=user_id,
    )
    return len(entries)


def derivation_for(symbol: str, user_id: str | None = None) -> dict:
    entries = ledger_store.list_entries(symbol=symbol, user_id=user_id)
    return explain_position(entries, symbol=symbol.strip().upper())


def _duplicate_key(entry: LedgerEntry) -> tuple:
    return (
        entry.symbol.strip().upper(),
        entry.kind.value,
        entry.traded_on,
        round(entry.quantity, 8),
        round(entry.price, 6),
    )


def mark_duplicates(parsed, user_id: str | None = None) -> None:
    existentes: dict[tuple, int] = {}
    for entry in ledger_store.list_entries(user_id=user_id):
        if entry.id is not None:
            existentes.setdefault(_duplicate_key(entry), entry.id)

    for row in parsed.rows:
        row.duplicate_of = existentes.get(_duplicate_key(row.entry))


def import_entries(entries: list[LedgerEntry], user_id: str | None = None) -> list[int]:
    if not entries:
        return []

    ids = ledger_store.record_many(entries, source="import", user_id=user_id)
    audit_store.write(
        audit_store.LEDGER_WRITE,
        entity="import",
        summary=f"{len(ids)} operação(ões) importadas.",
        detail={"symbols": sorted({e.symbol for e in entries})},
        user_id=user_id,
    )
    return ids
