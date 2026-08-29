from __future__ import annotations

import time

from sqlalchemy import delete, select

from app.core.database import db_session
from app.models.db_models import RevokedTokenDb, SessionCutDb


def revoke_jti(jti: str, user_id: str, expires_at: float) -> None:
    with db_session() as session:
        if session.get(RevokedTokenDb, jti) is not None:
            return
        session.add(
            RevokedTokenDb(
                jti=jti,
                user_id=user_id,
                revoked_at=time.time(),
                expires_at=expires_at,
            )
        )


def is_revoked(jti: str) -> bool:
    with db_session() as session:
        return session.get(RevokedTokenDb, jti) is not None


def revoke_all_for_user(user_id: str) -> float:
    cutoff = time.time()
    with db_session() as session:
        row = session.get(SessionCutDb, user_id)
        if row is None:
            session.add(SessionCutDb(user_id=user_id, cut_at=cutoff))
        else:
            row.cut_at = cutoff
    return cutoff


def tokens_valid_from(user_id: str) -> float:
    with db_session() as session:
        row = session.execute(
            select(SessionCutDb.cut_at).where(SessionCutDb.user_id == user_id)
        ).scalar_one_or_none()
        return float(row or 0.0)


def purge_expired(now: float | None = None) -> int:
    moment = now if now is not None else time.time()
    with db_session() as session:
        result = session.execute(delete(RevokedTokenDb).where(RevokedTokenDb.expires_at <= moment))
        return int(result.rowcount or 0)
