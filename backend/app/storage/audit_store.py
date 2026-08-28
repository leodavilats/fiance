"""Log append-only: o que aconteceu na conta, sem update e sem delete.

A camada de escrita não expõe alteração nem remoção de propósito. Um log que
pode ser corrigido responde uma coisa ao usuário e outra ao auditor, que é o
oposto do motivo de existir. A única saída é a exclusão de conta, que varre
`audit_log` junto com o resto em `account_store`.
"""

from __future__ import annotations

import json
import logging
import time

from sqlalchemy import select

from app.core.context import get_current_user_id_or_none
from app.core.database import db_session
from app.models.db_models import AuditLogDb

logger = logging.getLogger("fiance.audit")

# Ações registradas. Fechada pelo mesmo motivo do dicionário de eventos: log
# com nome livre vira log que ninguém consegue consultar.
LOGIN = "login"
LOGOUT = "logout"
POSITION_WRITE = "position.write"
POSITION_DELETE = "position.delete"
POSITION_SELL = "position.sell"
LEDGER_WRITE = "ledger.write"
LEDGER_DELETE = "ledger.delete"
GOAL_WRITE = "goal.write"
ALERT_WRITE = "alert.write"
ALERT_DELETE = "alert.delete"
ACCOUNT_EXPORT = "account.export"
SUBSCRIPTION_TRIAL = "subscription.trial"
SUBSCRIPTION_GRANT = "subscription.grant"
SUBSCRIPTION_CANCEL = "subscription.cancel"
REFERRAL_REWARD = "referral.reward"
ACCOUNT_DELETE = "account.delete"


def write(
    action: str,
    entity: str = "",
    entity_id: str | int | None = None,
    summary: str = "",
    detail: dict | None = None,
    user_id: str | None = None,
) -> None:
    """Registra uma ação. Nunca derruba a operação que a originou."""
    uid = user_id or get_current_user_id_or_none()
    if not uid:
        return

    try:
        with db_session() as session:
            session.add(
                AuditLogDb(
                    user_id=uid,
                    action=action,
                    entity=entity,
                    entity_id=str(entity_id) if entity_id is not None else None,
                    summary=summary,
                    detail=json.dumps(detail or {}, ensure_ascii=False, default=str),
                    occurred_at=time.time(),
                )
            )
    except Exception:
        logger.warning("Falha ao gravar auditoria de %s para %s", action, uid, exc_info=True)


def read(
    user_id: str | None = None,
    action: str | None = None,
    limit: int = 100,
) -> list[dict]:
    uid = user_id or get_current_user_id_or_none()
    if not uid:
        return []

    with db_session() as session:
        stmt = select(AuditLogDb).where(AuditLogDb.user_id == uid)
        if action:
            stmt = stmt.where(AuditLogDb.action == action)
        stmt = stmt.order_by(AuditLogDb.occurred_at.desc(), AuditLogDb.id.desc()).limit(
            max(1, min(limit, 500))
        )

        out = []
        for row in session.execute(stmt).scalars():
            try:
                detail = json.loads(row.detail or "{}")
            except (TypeError, ValueError):
                detail = {}
            out.append(
                {
                    "id": row.id,
                    "action": row.action,
                    "entity": row.entity,
                    "entity_id": row.entity_id,
                    "summary": row.summary,
                    "detail": detail,
                    "occurred_at": row.occurred_at,
                }
            )
        return out
