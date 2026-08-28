"""Portabilidade e eliminação — os dois direitos do titular, num lugar só.

A lista de tabelas é explícita e não derivada por reflexão de propósito: uma
tabela nova com `user_id` tem que aparecer aqui, e o teste
`test_account_covers_every_user_table` falha enquanto não aparecer. Esquecer de
apagar é o modo de falha que ninguém percebe até ser tarde.
"""

from __future__ import annotations

import time

from sqlalchemy import delete, inspect, select

from app.core.database import db_session, engine
from app.models.db_models import (
    AuditLogDb,
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
    RevokedTokenDb,
    SectorGoalDb,
    TransactionDb,
    UsageCounterDb,
    User,
    WatchlistItemDb,
)

# Prazo declarado ao usuário na tela de exclusão. A remoção é síncrona; o prazo
# existe para backup e réplica, que é onde o dado ainda pode estar.
DELETION_SLA_DAYS = 30

# Ordem importa: dependentes antes de `users`.
USER_SCOPED_MODELS = (
    ("positions", PortfolioPosition),
    ("snapshots", PortfolioSnapshot),
    ("watchlist", WatchlistItemDb),
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
    ("usage_counters", UsageCounterDb),
    ("product_events", ProductEventDb),
    ("revoked_tokens", RevokedTokenDb),
)

# Tabelas sem `user_id` — não pertencem a ninguém e por isso não entram nem na
# exportação nem na exclusão.
# `instruments` é catálogo, não conta: o código da B3 não pertence a ninguém.
GLOBAL_TABLES = frozenset({"users", "job_locks", "cache_entries", "alembic_version", "instruments"})

# `session_cuts` guarda exatamente uma linha por titular e é o que mantém as
# sessões mortas depois da exclusão. Apagá-la junto reabriria a porta que a
# exclusão acabou de fechar, então ela fica — e não tem dado pessoal nenhum.
DELETION_EXCLUDED = frozenset({"session_cuts"})

# O que existe por operação e não por titular: a denylist de sessão é apagada
# junto, mas exportá-la não diria nada ao usuário.
EXPORT_EXCLUDED = frozenset({"revoked_tokens", "usage_counters"})


def _row_to_dict(row, model) -> dict:
    return {column.key: getattr(row, column.key) for column in inspect(model).mapper.column_attrs}


def export_account(user_id: str) -> dict:
    """Tudo que é do usuário, em JSON, sem gate de plano.

    Portabilidade é direito do titular e exigência de loja: nunca atrás de
    assinatura, nunca parcial.
    """
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
    """Apaga tudo que é do titular e deixa a linha de `users` como lápide.

    Apagar a linha inteira ressuscitaria a conta: `_ensure_user` recria o
    titular na primeira escrita, e sem lápide não haveria como distinguir uma
    conta excluída de uma nunca criada. Então o dado pessoal some — e-mail, nome,
    foto — e sobra o identificador pseudônimo do Google com a data da exclusão.
    O corte de sessão vive em `session_cuts` e não é tocado aqui.
    """
    moment = now if now is not None else time.time()
    removed: dict[str, int] = {}
    with db_session() as session:
        for label, model in USER_SCOPED_MODELS:
            result = session.execute(delete(model).where(model.user_id == user_id))
            removed[label] = int(result.rowcount or 0)

        user = session.get(User, user_id)
        if user is not None:
            user.email = ""
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
    """Tabelas do schema real que têm coluna de titular — a fonte do teste."""
    inspector = inspect(engine)
    out = set()
    for table in inspector.get_table_names():
        if table in GLOBAL_TABLES or table in DELETION_EXCLUDED:
            continue
        columns = {column["name"] for column in inspector.get_columns(table)}
        if "user_id" in columns:
            out.add(table)
    return out
