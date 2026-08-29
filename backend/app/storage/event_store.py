from __future__ import annotations

import json
import time

from sqlalchemy import delete, func, select

from app.core.brt import to_brt
from app.core.database import db_session
from app.models.db_models import ProductEventDb

EVENT_RETENTION_DAYS = 400


def record(
    user_id: str,
    name: str,
    props: dict[str, str],
    platform: str,
    occurred_at: float | None = None,
) -> None:
    moment = occurred_at if occurred_at is not None else time.time()
    with db_session() as session:
        session.add(
            ProductEventDb(
                user_id=user_id,
                name=name,
                occurred_at=moment,
                day=to_brt(moment).strftime("%Y-%m-%d"),
                platform=platform,
                props=json.dumps(props, ensure_ascii=False, sort_keys=True),
            )
        )


def first_occurrence(user_id: str, name: str) -> float | None:
    with db_session() as session:
        return session.execute(
            select(func.min(ProductEventDb.occurred_at)).where(
                ProductEventDb.user_id == user_id,
                ProductEventDb.name == name,
            )
        ).scalar_one_or_none()


def has_event(user_id: str, name: str) -> bool:
    return first_occurrence(user_id, name) is not None


def users_with(name: str, since: float | None = None) -> set[str]:
    with db_session() as session:
        stmt = select(ProductEventDb.user_id).where(ProductEventDb.name == name).distinct()
        if since is not None:
            stmt = stmt.where(ProductEventDb.occurred_at >= since)
        return {row[0] for row in session.execute(stmt)}


def first_seen_by_user(since: float | None = None) -> dict[str, float]:
    with db_session() as session:
        stmt = select(ProductEventDb.user_id, func.min(ProductEventDb.occurred_at)).group_by(
            ProductEventDb.user_id
        )
        if since is not None:
            stmt = stmt.having(func.min(ProductEventDb.occurred_at) >= since)
        return {row[0]: float(row[1]) for row in session.execute(stmt)}


def first_by_user(name: str) -> dict[str, float]:
    with db_session() as session:
        rows = session.execute(
            select(ProductEventDb.user_id, func.min(ProductEventDb.occurred_at))
            .where(ProductEventDb.name == name)
            .group_by(ProductEventDb.user_id)
        )
        return {row[0]: float(row[1]) for row in rows}


def active_days_by_user(since: float) -> dict[str, set[str]]:
    with db_session() as session:
        rows = session.execute(
            select(ProductEventDb.user_id, ProductEventDb.day)
            .where(ProductEventDb.occurred_at >= since)
            .distinct()
        )
        out: dict[str, set[str]] = {}
        for user_id, day in rows:
            out.setdefault(user_id, set()).add(day)
        return out


def counts_by_name(since: float | None = None) -> dict[str, int]:
    with db_session() as session:
        stmt = select(ProductEventDb.name, func.count()).group_by(ProductEventDb.name)
        if since is not None:
            stmt = stmt.where(ProductEventDb.occurred_at >= since)
        return {row[0]: int(row[1]) for row in session.execute(stmt)}


def counts_by_prop(name: str, prop: str, since: float | None = None) -> dict[str, int]:
    with db_session() as session:
        stmt = select(ProductEventDb.props).where(ProductEventDb.name == name)
        if since is not None:
            stmt = stmt.where(ProductEventDb.occurred_at >= since)
        out: dict[str, int] = {}
        for (raw,) in session.execute(stmt):
            try:
                value = json.loads(raw or "{}").get(prop)
            except (TypeError, ValueError):
                value = None
            key = str(value) if value is not None else "(sem origem)"
            out[key] = out.get(key, 0) + 1
        return out


def delete_for_user(user_id: str) -> int:
    with db_session() as session:
        return int(
            session.execute(
                delete(ProductEventDb).where(ProductEventDb.user_id == user_id)
            ).rowcount
            or 0
        )


def purge_old(now: float | None = None) -> int:
    moment = now if now is not None else time.time()
    cutoff = moment - EVENT_RETENTION_DAYS * 86400
    with db_session() as session:
        return int(
            session.execute(
                delete(ProductEventDb).where(ProductEventDb.occurred_at < cutoff)
            ).rowcount
            or 0
        )
