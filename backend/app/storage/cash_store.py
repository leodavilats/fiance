from __future__ import annotations

import time

from sqlalchemy import select

from app.cashflow import CashEntry, CashKind, Debt
from app.core.context import get_current_user_id, get_request_session
from app.core.database import SessionLocal, ensure_initialized
from app.core.errors import NotFoundError
from app.core.money import money, to_float
from app.models.db_models import CashEntryDb, DebtDb


def _with_session(fn, user_id: str | None = None):
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


def _para_dominio(row: CashEntryDb) -> CashEntry:
    return CashEntry(
        kind=CashKind(row.kind),
        category=row.category,
        description=row.description,
        amount=to_float(row.amount),
        due_on=row.due_on,
        paid_on=row.paid_on,
        id=row.id,
        recurrence_id=row.recurrence_id,
        derived=row.derived_from is not None,
    )


def list_entries(user_id: str | None = None) -> list[CashEntry]:
    def run(session, uid):
        rows = session.scalars(
            select(CashEntryDb).where(CashEntryDb.user_id == uid).order_by(CashEntryDb.id)
        ).all()
        return [_para_dominio(r) for r in rows]

    return _with_session(run, user_id)


def add_entry(entry: CashEntry, source: str = "manual", user_id: str | None = None) -> int:
    def run(session, uid):
        agora = time.time()
        row = CashEntryDb(
            user_id=uid,
            kind=entry.kind.value,
            category=entry.category,
            description=entry.description.strip(),
            amount=money(entry.amount),
            due_on=entry.due_on,
            paid_on=entry.paid_on,
            recurrence_id=entry.recurrence_id,
            derived_from=entry.metadata.get("derived_from") if entry.derived else None,
            source=source,
            created_at=agora,
            updated_at=agora,
        )
        session.add(row)
        session.flush()
        return int(row.id)

    return _with_session(run, user_id)


def mark_paid(entry_id: int, paid_on: str, user_id: str | None = None) -> None:
    def run(session, uid):
        row = session.scalars(
            select(CashEntryDb).where(CashEntryDb.id == entry_id, CashEntryDb.user_id == uid)
        ).first()
        if row is None:
            raise NotFoundError(f"Lançamento {entry_id} não existe.")

        row.paid_on = paid_on
        row.updated_at = time.time()

    _with_session(run, user_id)


def delete_entry(entry_id: int, user_id: str | None = None) -> None:
    def run(session, uid):
        row = session.scalars(
            select(CashEntryDb).where(CashEntryDb.id == entry_id, CashEntryDb.user_id == uid)
        ).first()
        if row is None:
            raise NotFoundError(f"Lançamento {entry_id} não existe.")

        if row.derived_from is not None:
            raise NotFoundError(
                "Lançamento derivado do razão não se apaga aqui: ele é projeção, e some quando "
                "o lançamento de origem sai."
            )

        session.delete(row)

    _with_session(run, user_id)


def replace_derived(entries: list[CashEntry], user_id: str | None = None) -> int:
    """Reescreve as entradas derivadas do razão, do zero.

    Derivado é projeção, e projeção se **reconstrói** — não se atualiza item a item. É o mesmo
    padrão de `rebuild_projection` na carteira: apagar e refazer é a única forma de a segunda
    leitura não divergir da primeira em silêncio.
    """

    def run(session, uid):
        antigos = session.scalars(
            select(CashEntryDb).where(
                CashEntryDb.user_id == uid, CashEntryDb.derived_from.is_not(None)
            )
        ).all()
        for row in antigos:
            session.delete(row)
        session.flush()

        agora = time.time()
        for e in entries:
            session.add(
                CashEntryDb(
                    user_id=uid,
                    kind=e.kind.value,
                    category=e.category,
                    description=e.description.strip(),
                    amount=money(e.amount),
                    due_on=e.due_on,
                    paid_on=e.paid_on,
                    recurrence_id=None,
                    derived_from=e.metadata.get("derived_from", "ledger"),
                    source="derived",
                    created_at=agora,
                    updated_at=agora,
                )
            )

        return len(entries)

    return _with_session(run, user_id)


def _debt_para_dominio(row: DebtDb) -> Debt:
    return Debt(
        kind=row.kind,
        description=row.description,
        balance=to_float(row.balance),
        monthly_rate=row.monthly_rate,
        id=row.id,
    )


def list_debts(user_id: str | None = None, include_settled: bool = False) -> list[Debt]:
    def run(session, uid):
        consulta = select(DebtDb).where(DebtDb.user_id == uid)
        if not include_settled:
            consulta = consulta.where(DebtDb.settled_at.is_(None))
        rows = session.scalars(consulta.order_by(DebtDb.id)).all()
        return [_debt_para_dominio(r) for r in rows]

    return _with_session(run, user_id)


def add_debt(debt: Debt, user_id: str | None = None) -> int:
    def run(session, uid):
        agora = time.time()
        row = DebtDb(
            user_id=uid,
            kind=debt.kind,
            description=debt.description.strip(),
            balance=money(debt.balance),
            monthly_rate=debt.monthly_rate,
            created_at=agora,
            updated_at=agora,
        )
        session.add(row)
        session.flush()
        return int(row.id)

    return _with_session(run, user_id)


def settle_debt(debt_id: int, user_id: str | None = None) -> None:
    def run(session, uid):
        row = session.scalars(
            select(DebtDb).where(DebtDb.id == debt_id, DebtDb.user_id == uid)
        ).first()
        if row is None:
            raise NotFoundError(f"Dívida {debt_id} não existe.")

        row.settled_at = time.time()
        row.updated_at = time.time()

    _with_session(run, user_id)
