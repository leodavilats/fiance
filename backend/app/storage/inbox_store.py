from __future__ import annotations

import time
from dataclasses import dataclass

from sqlalchemy import func, select, update

from app.core.context import get_current_user_id, get_request_session
from app.core.database import SessionLocal, ensure_initialized
from app.core.pagination import apply_keyset
from app.models.db_models import InboxItemDb


@dataclass(frozen=True)
class InboxNotice:
    dedup_key: str
    kind: str
    severity: str
    title: str
    detail: str
    ticker: str | None = None
    action: str | None = None
    action_label: str | None = None


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


def _row(row: InboxItemDb) -> dict:
    return {
        "id": row.id,
        "kind": row.kind,
        "severity": row.severity,
        "title": row.title,
        "detail": row.detail,
        "ticker": row.ticker,
        "action": row.action,
        "action_label": row.action_label,
        "created_at": row.created_at,
        "read_at": row.read_at,
    }


def record(notices: list[InboxNotice], user_id: str | None = None, now: float | None = None) -> int:
    if not notices:
        return 0

    def body(session, uid: str) -> int:
        chaves = {n.dedup_key for n in notices}
        existentes = set(
            session.scalars(
                select(InboxItemDb.dedup_key).where(
                    InboxItemDb.user_id == uid, InboxItemDb.dedup_key.in_(chaves)
                )
            )
        )
        momento = now or time.time()
        novos = 0
        for notice in notices:
            if notice.dedup_key in existentes:
                continue
            existentes.add(notice.dedup_key)
            session.add(
                InboxItemDb(
                    user_id=uid,
                    dedup_key=notice.dedup_key,
                    kind=notice.kind,
                    severity=notice.severity,
                    title=notice.title,
                    detail=notice.detail,
                    ticker=notice.ticker,
                    action=notice.action,
                    action_label=notice.action_label,
                    created_at=momento,
                )
            )
            novos += 1
        return novos

    return _with_session(body, user_id)


def list_items(limit: int, cursor: str | None = None, kinds: list[str] | None = None) -> list[dict]:
    def body(session, uid: str) -> list[dict]:
        stmt = select(InboxItemDb).where(InboxItemDb.user_id == uid)
        if kinds:
            stmt = stmt.where(InboxItemDb.kind.in_(kinds))
        stmt = apply_keyset(stmt, InboxItemDb.created_at, InboxItemDb.id, cursor).limit(limit + 1)
        return [_row(r) for r in session.scalars(stmt)]

    return _with_session(body)


def unread_count(user_id: str | None = None) -> int:
    def body(session, uid: str) -> int:
        return session.scalar(
            select(func.count(InboxItemDb.id)).where(
                InboxItemDb.user_id == uid, InboxItemDb.read_at.is_(None)
            )
        )

    return _with_session(body, user_id)


def mark_read(ids: list[int] | None, now: float | None = None) -> int:
    def body(session, uid: str) -> int:
        stmt = (
            update(InboxItemDb)
            .where(InboxItemDb.user_id == uid, InboxItemDb.read_at.is_(None))
            .values(read_at=now or time.time())
        )
        if ids is not None:
            stmt = stmt.where(InboxItemDb.id.in_(ids))
        return session.execute(stmt).rowcount or 0

    return _with_session(body)
