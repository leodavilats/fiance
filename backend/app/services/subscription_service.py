"""Ciclo de vida da assinatura: trial, concessão, degradação.

O direito mora no backend, ligado ao `user_id`; os clientes só consultam.
Nenhuma decisão de acesso acontece no dispositivo — cliente adulterado não pode
virar assinante — e é isso que permite vender na web e liberar no app sem
migrar ninguém quando o canal mudar.
"""

from __future__ import annotations

import logging
import time

from app.core.database import db_session
from app.entitlement.resolve import TRIAL_DAYS
from app.models.db_models import ProcessedWebhookDb, SubscriptionDb
from app.storage import audit_store, event_store, portfolio_store

logger = logging.getLogger("fiance.subscription")

#: Preço de tabela, em centavos. Quem tem `locked` não é alcançado por mudanças
#: aqui — é o que torna a promessa de preço travado verificável.
PRICE_MONTHLY_CENTS = 1990
PRICE_YEARLY_CENTS = 17990
PRICE_FOUNDER_YEARLY_CENTS = 14990


def _row(session, user_id: str) -> SubscriptionDb:
    row = session.get(SubscriptionDb, user_id)
    if row is None:
        portfolio_store.ensure_user(session, user_id)
        row = SubscriptionDb(user_id=user_id, created_at=time.time(), updated_at=time.time())
        session.add(row)
        session.flush()
    return row


def start_trial(user_id: str, now: float | None = None) -> dict:
    """Começa o trial de 14 dias. Idempotente.

    O gatilho é a **primeira posição salva**, não a criação da conta: trial que
    expira antes de a pessoa ter uma carteira para analisar é trial
    desperdiçado — ela nunca chega a ver o que estaria comprando.
    """
    moment = now if now is not None else time.time()

    with db_session() as session:
        row = _row(session, user_id)

        if row.trial_started_at is not None:
            return _as_dict(row)

        row.trial_started_at = moment
        row.trial_ends_at = moment + TRIAL_DAYS * 86400
        row.status = "trialing"
        row.updated_at = moment
        resultado = _as_dict(row)

    event_store.record(user_id, "trial_started", {}, platform="server")
    audit_store.write(
        audit_store.SUBSCRIPTION_TRIAL,
        entity="subscription",
        summary=f"Trial de {TRIAL_DAYS} dias iniciado.",
        user_id=user_id,
    )
    return resultado


def grant(
    user_id: str,
    plan_code: str,
    price_cents: int,
    interval: str = "monthly",
    provider: str = "stripe",
    external_id: str | None = None,
    period_end: float | None = None,
    locked: bool = False,
    now: float | None = None,
) -> dict:
    """Concede o direito. É o que o webhook e a concessão manual chamam.

    `price_cents` é gravado, não derivado da tabela vigente: reajustar o preço
    de tabela depois não pode alcançar quem contratou antes, e a única forma de
    garantir isso é a assinatura carregar o próprio preço.
    """
    moment = now if now is not None else time.time()

    with db_session() as session:
        row = _row(session, user_id)
        row.plan_code = plan_code
        row.status = "active"
        row.price_cents = price_cents
        row.interval = interval
        row.provider = provider
        row.external_id = external_id
        row.current_period_end = period_end
        row.locked = locked
        row.granted_at = row.granted_at or moment
        row.cancelled_at = None
        row.updated_at = moment
        resultado = _as_dict(row)

    event_store.record(
        user_id,
        "subscription_started",
        {"plan": plan_code, "channel": provider},
        platform="server",
    )
    audit_store.write(
        audit_store.SUBSCRIPTION_GRANT,
        entity="subscription",
        summary=f"Plano {plan_code} concedido a {price_cents / 100:.2f}.",
        detail={"provider": provider, "locked": locked},
        user_id=user_id,
    )
    return resultado


def cancel(user_id: str, reason: str = "", now: float | None = None) -> dict:
    """Cancela sem apagar nada.

    Assinatura expirada degrada para Free e a carteira continua acessível.
    Cancelar Premium não é cancelar conta — tratar como se fosse produz pedido
    de exclusão em massa no primeiro churn.
    """
    moment = now if now is not None else time.time()

    with db_session() as session:
        row = _row(session, user_id)
        row.status = "cancelled"
        row.cancelled_at = moment
        # Encerra o trial junto: cancelar significa "não quero", e deixar o
        # trial correndo faria o cancelamento não cancelar nada por até 14 dias.
        if row.trial_ends_at is not None and row.trial_ends_at > moment:
            row.trial_ends_at = moment
        row.updated_at = moment
        resultado = _as_dict(row)

    event_store.record(
        user_id, "subscription_cancelled", {"reason": reason or "none"}, platform="server"
    )
    audit_store.write(
        audit_store.SUBSCRIPTION_CANCEL,
        entity="subscription",
        summary="Assinatura cancelada. Nenhum dado foi removido.",
        user_id=user_id,
    )
    return resultado


def already_processed(provider: str, event_id: str) -> bool:
    with db_session() as session:
        return session.get(ProcessedWebhookDb, (provider, event_id)) is not None


def mark_processed(provider: str, event_id: str, summary: str = "") -> None:
    """Marca o evento como visto. Chamado **depois** de aplicar o efeito.

    O provedor reenvia até receber 200, por desenho. Sem esta tabela, o reenvio
    concederia direito duas vezes — e no caso de crédito de meses, daria meses
    de graça a cada retentativa.
    """
    with db_session() as session:
        if session.get(ProcessedWebhookDb, (provider, event_id)) is not None:
            return
        session.add(
            ProcessedWebhookDb(
                provider=provider,
                event_id=event_id,
                processed_at=time.time(),
                summary=summary[:200],
            )
        )


def get(user_id: str) -> dict:
    with db_session() as session:
        row = session.get(SubscriptionDb, user_id)
        return _as_dict(row) if row is not None else _empty(user_id)


def _empty(user_id: str) -> dict:
    return {
        "user_id": user_id,
        "plan_code": "free",
        "status": "none",
        "price_cents": 0,
        "interval": "monthly",
        "locked": False,
        "trial_started_at": None,
        "trial_ends_at": None,
        "current_period_end": None,
        "cancelled_at": None,
        "provider": "none",
    }


def _as_dict(row: SubscriptionDb) -> dict:
    return {
        "user_id": row.user_id,
        "plan_code": row.plan_code,
        "status": row.status,
        "price_cents": row.price_cents,
        "interval": row.interval,
        "locked": bool(row.locked),
        "trial_started_at": row.trial_started_at,
        "trial_ends_at": row.trial_ends_at,
        "current_period_end": row.current_period_end,
        "cancelled_at": row.cancelled_at,
        "provider": row.provider,
    }
