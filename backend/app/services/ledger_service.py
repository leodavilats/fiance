from __future__ import annotations

import logging
from collections.abc import Iterable

from app.core.brt import now_brt
from app.ledger import LedgerEntry, TransactionKind, explain_position, project_positions
from app.ledger.projection import PositionProjection
from app.storage import audit_store, ledger_store, portfolio_store

logger = logging.getLogger("fiance.ledger")

QUANTITY_TOLERANCE = 1e-6
PRICE_TOLERANCE = 1e-4


def today_brt() -> str:
    return now_brt().strftime("%Y-%m-%d")


def record_position_state(
    ticker: str,
    quantity: float,
    avg_price: float,
    traded_on: str | None = None,
    category: str | None = None,
    user_id: str | None = None,
) -> None:
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
    rebuild_projection(symbol=ticker, category=category, user_id=user_id)


def record_sale(
    ticker: str,
    quantity: float,
    price: float,
    fees: float = 0.0,
    traded_on: str | None = None,
    user_id: str | None = None,
) -> None:
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
    rebuild_projection(symbol=ticker, user_id=user_id)


def record_removal(ticker: str, user_id: str | None = None) -> None:
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
    rebuild_projection(symbol=ticker, user_id=user_id)


def record_entry(entry: LedgerEntry, source: str = "manual", user_id: str | None = None) -> int:
    entry_id = ledger_store.record(entry, source=source, user_id=user_id)
    rebuild_projection(symbol=entry.symbol, user_id=user_id)
    return entry_id


def record_entries(
    entries: list[LedgerEntry],
    source: str = "manual",
    user_id: str | None = None,
) -> list[int]:
    if not entries:
        return []

    ids = ledger_store.record_many(entries, source=source, user_id=user_id)
    rebuild_projection(symbols={e.symbol for e in entries}, user_id=user_id)
    return ids


def delete_entry(entry_id: int, user_id: str | None = None) -> str:
    symbol = ledger_store.delete_entry(entry_id, user_id=user_id)
    rebuild_projection(symbol=symbol, user_id=user_id)
    return symbol


def rebuild_projection(
    symbol: str | None = None,
    category: str | None = None,
    user_id: str | None = None,
    symbols: Iterable[str] | None = None,
) -> int:
    alvos: set[str] | None = None
    if symbols is not None:
        alvos = {s.strip().upper() for s in symbols if s and s.strip()}
    elif symbol:
        alvos = {symbol.strip().upper()}

    projetadas = project(user_id)
    categorias = {
        item["ticker"]: item["category"] for item in portfolio_store.list_positions(user_id)
    }
    if symbol and category:
        categorias[symbol.strip().upper()] = category

    escritas = 0
    for ticker, estado in projetadas.items():
        if alvos is not None and ticker not in alvos:
            continue
        if estado.is_open:
            portfolio_store.upsert_position(
                ticker=ticker,
                quantity=estado.quantity,
                avg_price=estado.avg_price,
                category=categorias.get(ticker, "auto"),
                user_id=user_id,
            )
        else:
            portfolio_store.delete_position(ticker, user_id=user_id)
        escritas += 1

    for ticker in categorias:
        if alvos is not None and ticker not in alvos:
            continue
        if ticker not in projetadas:
            portfolio_store.delete_position(ticker, user_id=user_id)
            escritas += 1

    return escritas


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
    rebuild_projection(symbols={e.symbol for e in entries}, user_id=user_id)
    audit_store.write(
        audit_store.LEDGER_WRITE,
        entity="import",
        summary=f"{len(ids)} operação(ões) importadas.",
        detail={"symbols": sorted({e.symbol for e in entries})},
        user_id=user_id,
    )
    return ids
