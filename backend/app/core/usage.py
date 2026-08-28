"""Contador por usuário, recurso e janela.

Uma primitiva só para dois tetos que sempre foram o mesmo problema: abuso
(N chamadas por minuto numa rota) e plano (5 páginas de ativo por mês). A
granularidade não é uma coluna, é o formato de `window_key` — trocar de janela
não muda o schema.

O mês é o mês calendário **brasileiro**, pela mesma razão que a isenção de IR
é: o usuário conta o mês dele, não o do UTC.
"""

from __future__ import annotations

import time

from sqlalchemy import delete, select

from app.core.brt import month_key, to_brt
from app.core.database import db_session
from app.models.db_models import UsageCounterDb

MINUTE = 60.0
HOUR = 3600.0
DAY = 86400.0


def minute_window(timestamp: float | None = None) -> str:
    moment = timestamp if timestamp is not None else time.time()
    return to_brt(moment).strftime("%Y-%m-%dT%H:%M")


def hour_window(timestamp: float | None = None) -> str:
    moment = timestamp if timestamp is not None else time.time()
    return to_brt(moment).strftime("%Y-%m-%dT%H")


def day_window(timestamp: float | None = None) -> str:
    moment = timestamp if timestamp is not None else time.time()
    return to_brt(moment).strftime("%Y-%m-%d")


def month_window(timestamp: float | None = None) -> str:
    moment = timestamp if timestamp is not None else time.time()
    return month_key(moment)


def increment(
    user_id: str,
    resource: str,
    window_key: str,
    ttl_seconds: float,
    amount: int = 1,
) -> int:
    """Soma no contador da janela e devolve o valor já somado."""
    now = time.time()
    with db_session() as session:
        row = session.get(UsageCounterDb, (user_id, resource, window_key))
        if row is None:
            row = UsageCounterDb(
                user_id=user_id,
                resource=resource,
                window_key=window_key,
                count=amount,
                expires_at=now + ttl_seconds,
                updated_at=now,
            )
            session.add(row)
            return amount

        row.count += amount
        row.updated_at = now
        row.expires_at = max(row.expires_at, now + ttl_seconds)
        return int(row.count)


def current(user_id: str, resource: str, window_key: str) -> int:
    with db_session() as session:
        value = session.execute(
            select(UsageCounterDb.count).where(
                UsageCounterDb.user_id == user_id,
                UsageCounterDb.resource == resource,
                UsageCounterDb.window_key == window_key,
            )
        ).scalar_one_or_none()
        return int(value or 0)


def reset(user_id: str, resource: str, window_key: str | None = None) -> int:
    """Zera o contador — usado por manutenção e por concessão de cortesia."""
    with db_session() as session:
        stmt = delete(UsageCounterDb).where(
            UsageCounterDb.user_id == user_id,
            UsageCounterDb.resource == resource,
        )
        if window_key is not None:
            stmt = stmt.where(UsageCounterDb.window_key == window_key)
        return int(session.execute(stmt).rowcount or 0)


def purge_expired(now: float | None = None) -> int:
    moment = now if now is not None else time.time()
    with db_session() as session:
        result = session.execute(delete(UsageCounterDb).where(UsageCounterDb.expires_at <= moment))
        return int(result.rowcount or 0)
