"""Persistência do livro-razão, multi-tenant como o resto.

Escreve e lê lançamentos; a matemática mora em `app/ledger`, que não conhece
banco. A resolução de instrumento acontece aqui porque depende do estado do
catálogo, não da conta.
"""

from __future__ import annotations

import time

from sqlalchemy import delete, select

from app.core.context import get_current_user_id, get_request_session
from app.core.database import SessionLocal, ensure_initialized
from app.core.errors import NotFoundError
from app.core.pagination import apply_keyset
from app.ledger import LedgerEntry, TransactionKind
from app.models.db_models import InstrumentDb, TransactionDb

# Fim de janela aberto: o dono atual do código.
OPEN_ENDED = None


def _with_session(fn, user_id: str | None = None):
    """Reaproveita a sessão da requisição; fora dela, abre e commita a própria."""
    ensure_initialized()
    uid = user_id or get_current_user_id()

    ambient = get_request_session()
    if ambient is not None:
        result = fn(ambient, uid)
        ambient.flush()
        return result

    session = SessionLocal()
    try:
        result = fn(session, uid)
        session.commit()
        return result
    finally:
        session.close()


# --------------------------------------------------------------------------
# Instrumentos
# --------------------------------------------------------------------------


def resolve_instrument(session, symbol: str, traded_on: str) -> InstrumentDb:
    """Instrumento dono do símbolo na data da operação.

    Se ninguém reivindicou o código ainda, cria o dono atual. Um código
    reaproveitado pela B3 é registrado fechando a janela do antigo e abrindo a
    do novo — e aí operações antigas continuam apontando para o instrumento
    certo, que é o ponto.
    """
    normalized = symbol.strip().upper()

    rows = (
        session.execute(select(InstrumentDb).where(InstrumentDb.symbol == normalized))
        .scalars()
        .all()
    )

    for row in rows:
        starts_before = row.valid_from <= traded_on
        ends_after = row.valid_to is OPEN_ENDED or traded_on <= row.valid_to
        if starts_before and ends_after:
            return row

    created = InstrumentDb(
        symbol=normalized,
        valid_from="1900-01-01" if not rows else traded_on,
        valid_to=OPEN_ENDED,
        created_at=time.time(),
    )
    session.add(created)
    session.flush()
    return created


def reassign_symbol(symbol: str, from_day: str, name: str = "", asset_type: str = "br_stock"):
    """Registra que a B3 passou o código para outra companhia em `from_day`."""
    ensure_initialized()
    session = get_request_session() or SessionLocal()
    owns_session = get_request_session() is None
    try:
        normalized = symbol.strip().upper()
        current = (
            session.execute(
                select(InstrumentDb).where(
                    InstrumentDb.symbol == normalized,
                    InstrumentDb.valid_to.is_(None),
                )
            )
            .scalars()
            .first()
        )
        if current is not None:
            current.valid_to = from_day

        successor = InstrumentDb(
            symbol=normalized,
            name=name,
            asset_type=asset_type,
            valid_from=from_day,
            valid_to=OPEN_ENDED,
            created_at=time.time(),
        )
        session.add(successor)
        session.flush()
        if owns_session:
            session.commit()
        return successor.id
    finally:
        if owns_session:
            session.close()


# --------------------------------------------------------------------------
# Lançamentos
# --------------------------------------------------------------------------


def _to_entry(row: TransactionDb) -> LedgerEntry:
    return LedgerEntry(
        kind=TransactionKind(row.kind),
        symbol=row.symbol,
        traded_on=row.traded_on,
        quantity=row.quantity,
        price=row.price,
        fees=row.fees,
        ratio_from=row.ratio_from,
        ratio_to=row.ratio_to,
        amount=row.amount,
        id=row.id,
        instrument_id=row.instrument_id,
        note=row.note,
    )


def record(entry: LedgerEntry, source: str = "manual", user_id: str | None = None) -> int:
    """Grava um lançamento e devolve o id."""

    def body(session, uid: str) -> int:
        from app.storage.portfolio_store import _ensure_user

        _ensure_user(session, uid)
        instrument = resolve_instrument(session, entry.symbol, entry.traded_on)
        row = TransactionDb(
            user_id=uid,
            instrument_id=instrument.id,
            symbol=entry.symbol.strip().upper(),
            kind=entry.kind.value,
            quantity=entry.quantity,
            price=entry.price,
            fees=entry.fees,
            ratio_from=entry.ratio_from,
            ratio_to=entry.ratio_to,
            amount=entry.amount,
            traded_on=entry.traded_on,
            source=source,
            note=entry.note,
            created_at=time.time(),
        )
        session.add(row)
        session.flush()
        return row.id

    return _with_session(body, user_id)


def record_many(
    entries: list[LedgerEntry], source: str = "import", user_id: str | None = None
) -> list[int]:
    """Grava um lote inteiro ou nenhum — importação é atômica."""

    def body(session, uid: str) -> list[int]:
        from app.storage.portfolio_store import _ensure_user

        _ensure_user(session, uid)
        ids = []
        for entry in entries:
            instrument = resolve_instrument(session, entry.symbol, entry.traded_on)
            row = TransactionDb(
                user_id=uid,
                instrument_id=instrument.id,
                symbol=entry.symbol.strip().upper(),
                kind=entry.kind.value,
                quantity=entry.quantity,
                price=entry.price,
                fees=entry.fees,
                ratio_from=entry.ratio_from,
                ratio_to=entry.ratio_to,
                amount=entry.amount,
                traded_on=entry.traded_on,
                source=source,
                note=entry.note,
                created_at=time.time(),
            )
            session.add(row)
            session.flush()
            ids.append(row.id)
        return ids

    return _with_session(body, user_id)


def list_entries(
    symbol: str | None = None,
    user_id: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
    descending: bool = False,
) -> list[LedgerEntry]:
    """Lançamentos do usuário.

    A ordem padrão é **crescente** porque a projeção do razão depende dela: o
    preço médio é uma dobra na ordem em que as operações aconteceram. A listagem
    de tela pede `descending=True`, que é a ordem de leitura.

    Devolve `limit + 1` quando há limite — a linha extra é como quem chama
    descobre que existe próxima página.
    """

    def body(session, uid: str) -> list[LedgerEntry]:
        stmt = select(TransactionDb).where(TransactionDb.user_id == uid)
        if symbol:
            stmt = stmt.where(TransactionDb.symbol == symbol.strip().upper())
        stmt = apply_keyset(stmt, TransactionDb.traded_on, TransactionDb.id, cursor, descending)
        if limit:
            stmt = stmt.limit(limit + 1)
        return [_to_entry(row) for row in session.execute(stmt).scalars()]

    return _with_session(body, user_id)


def delete_entry(entry_id: int, user_id: str | None = None) -> None:
    def body(session, uid: str) -> None:
        row = session.get(TransactionDb, entry_id)
        if row is None or row.user_id != uid:
            raise NotFoundError("Lançamento não encontrado.")
        session.delete(row)

    _with_session(body, user_id)


def delete_symbol_entries(symbol: str, user_id: str | None = None) -> int:
    def body(session, uid: str) -> int:
        result = session.execute(
            delete(TransactionDb).where(
                TransactionDb.user_id == uid,
                TransactionDb.symbol == symbol.strip().upper(),
            )
        )
        return int(result.rowcount or 0)

    return _with_session(body, user_id)


def symbols(user_id: str | None = None) -> list[str]:
    def body(session, uid: str) -> list[str]:
        rows = session.execute(
            select(TransactionDb.symbol).where(TransactionDb.user_id == uid).distinct()
        )
        return sorted(row[0] for row in rows)

    return _with_session(body, user_id)
