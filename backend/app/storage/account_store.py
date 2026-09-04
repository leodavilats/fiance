from __future__ import annotations

import time

from sqlalchemy import delete, inspect, select

from app.core.database import db_session, engine
from app.models.db_models import (
    AuditLogDb,
    CheckoutSessionDb,
    ClosedTradeDb,
    DeviceTokenDb,
    DividendReceivedDb,
    FixedIncomePositionDb,
    FollowedSuggestionDb,
    GoalDb,
    NotifiedOpportunityDb,
    PortfolioPosition,
    PortfolioSnapshot,
    PreferencesDb,
    PriceAlertDb,
    ProductEventDb,
    ReferralCodeDb,
    ReferralDb,
    RevokedTokenDb,
    SectorGoalDb,
    SubscriptionDb,
    TransactionDb,
    UsageCounterDb,
    User,
)

DELETION_SLA_DAYS = 30

USER_SCOPED_MODELS = (
    ("positions", PortfolioPosition),
    ("snapshots", PortfolioSnapshot),
    ("goals", GoalDb),
    ("sector_goals", SectorGoalDb),
    ("preferences", PreferencesDb),
    ("closed_trades", ClosedTradeDb),
    ("notified_opportunities", NotifiedOpportunityDb),
    ("device_tokens", DeviceTokenDb),
    ("price_alerts", PriceAlertDb),
    ("fixed_income_positions", FixedIncomePositionDb),
    ("dividends_received", DividendReceivedDb),
    ("followed_suggestions", FollowedSuggestionDb),
    ("transactions", TransactionDb),
    ("audit_log", AuditLogDb),
    ("subscription", SubscriptionDb),
    ("checkout_sessions", CheckoutSessionDb),
    ("usage_counters", UsageCounterDb),
    ("product_events", ProductEventDb),
    ("revoked_tokens", RevokedTokenDb),
    ("referral_code", ReferralCodeDb),
    ("referrals_made", ReferralDb),
)

GLOBAL_TABLES = frozenset({"users", "job_locks", "cache_entries", "alembic_version", "instruments"})

DELETION_EXCLUDED = frozenset({"session_cuts"})

EXPORT_EXCLUDED = frozenset({"revoked_tokens", "usage_counters"})


def _row_to_dict(row, model) -> dict:
    return {column.key: getattr(row, column.key) for column in inspect(model).mapper.column_attrs}


def export_account(user_id: str) -> dict:
    with db_session() as session:
        user = session.get(User, user_id)
        payload: dict = {
            "exported_at": time.time(),
            "format_version": 1,
            "user": _row_to_dict(user, User) if user is not None else {"id": user_id},
            "data": {},
        }

        for label, model in USER_SCOPED_MODELS:
            if label in EXPORT_EXCLUDED:
                continue
            rows = session.execute(select(model).where(model.user_id == user_id)).scalars().all()
            payload["data"][label] = [_row_to_dict(row, model) for row in rows]

    return payload


def delete_account(user_id: str, now: float | None = None) -> dict:
    moment = now if now is not None else time.time()
    removed: dict[str, int] = {}
    with db_session() as session:
        for label, model in USER_SCOPED_MODELS:
            result = session.execute(delete(model).where(model.user_id == user_id))
            removed[label] = int(result.rowcount or 0)

        user = session.get(User, user_id)
        if user is not None:
            user.email = f"apagado+{user_id}@invalid"
            user.name = ""
            user.picture = ""
            user.onboarded_at = None
            user.deleted_at = moment
            removed["user"] = 1
        else:
            removed["user"] = 0

    return removed


def user_scoped_table_names() -> set[str]:
    return {model.__tablename__ for _, model in USER_SCOPED_MODELS}


def tables_with_user_column() -> set[str]:
    inspector = inspect(engine)
    out = set()
    for table in inspector.get_table_names():
        if table in GLOBAL_TABLES or table in DELETION_EXCLUDED:
            continue
        columns = {column["name"] for column in inspector.get_columns(table)}
        if "user_id" in columns:
            out.add(table)
    return out
