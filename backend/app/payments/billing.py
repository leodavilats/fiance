from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from app.core.config import get_settings
from app.core.database import db_session
from app.models.db_models import CheckoutSessionDb, SubscriptionDb
from app.services import subscription_service
from app.storage import event_store

from .provider import FakeProvider, PaymentProvider, WebhookEvent

logger = logging.getLogger("fiance.billing")


@dataclass(frozen=True)
class PlanOffer:
    code: str
    label: str
    price_cents: int
    interval: str
    monthly_equivalent_cents: int
    note: str = ""
    founder: bool = False

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "label": self.label,
            "price_cents": self.price_cents,
            "interval": self.interval,
            "monthly_equivalent_cents": self.monthly_equivalent_cents,
            "note": self.note,
            "founder": self.founder,
        }


OFFERS: tuple[PlanOffer, ...] = (
    PlanOffer(
        code="premium_monthly",
        label="Premium mensal",
        price_cents=subscription_service.PRICE_MONTHLY_CENTS,
        interval="monthly",
        monthly_equivalent_cents=subscription_service.PRICE_MONTHLY_CENTS,
        note="Cancele quando quiser. Seus dados continuam seus.",
    ),
    PlanOffer(
        code="premium_yearly",
        label="Premium anual",
        price_cents=subscription_service.PRICE_YEARLY_CENTS,
        interval="yearly",
        monthly_equivalent_cents=subscription_service.PRICE_YEARLY_CENTS // 12,
        note="Equivale a R$ 14,99 por mês.",
    ),
    PlanOffer(
        code="premium_founder",
        label="Fundador — preço travado",
        price_cents=subscription_service.PRICE_FOUNDER_YEARLY_CENTS,
        interval="yearly",
        monthly_equivalent_cents=subscription_service.PRICE_FOUNDER_YEARLY_CENTS // 12,
        note="Este preço não é reajustado enquanto a assinatura estiver ativa.",
        founder=True,
    ),
)

OFFERS_BY_CODE = {offer.code: offer for offer in OFFERS}

_provider: PaymentProvider | None = None


def provider() -> PaymentProvider:
    global _provider
    if _provider is None:
        settings = get_settings()
        _provider = FakeProvider(secret=settings.billing_webhook_secret)
    return _provider


def set_provider(novo: PaymentProvider | None) -> None:
    global _provider
    _provider = novo


def offers() -> list[dict]:
    return [offer.as_dict() for offer in OFFERS]


class UnknownPlanError(ValueError):
    pass


def start_checkout(user_id: str, plan_code: str) -> dict:
    offer = OFFERS_BY_CODE.get(plan_code)
    if offer is None:
        raise UnknownPlanError(
            f"Plano {plan_code!r} não existe. Disponíveis: {sorted(OFFERS_BY_CODE)}."
        )

    sessao = provider().create_checkout(
        user_id=user_id,
        plan_code=offer.code,
        price_cents=offer.price_cents,
        interval=offer.interval,
    )

    with db_session() as session:
        session.merge(
            CheckoutSessionDb(
                id=sessao.id,
                user_id=user_id,
                provider=sessao.provider,
                plan_code=offer.code,
                price_cents=offer.price_cents,
                interval=offer.interval,
                created_at=time.time(),
                expires_at=sessao.expires_at,
            )
        )

    event_store.record(
        user_id,
        "upgrade_started",
        {"plan": offer.code, "channel": sessao.provider},
        platform="server",
    )

    return {
        "session_id": sessao.id,
        "url": sessao.url,
        "provider": sessao.provider,
        "expires_at": sessao.expires_at,
        "plan": offer.as_dict(),
    }


class UnresolvedSubjectError(ValueError):
    pass


@dataclass(frozen=True)
class _Subject:
    user_id: str
    plan_code: str
    price_cents: int
    interval: str


def _resolve_subject(event: WebhookEvent) -> _Subject:
    with db_session() as session:
        if event.session_id:
            sessao = session.get(CheckoutSessionDb, event.session_id)
            if sessao is not None:
                return _Subject(
                    user_id=sessao.user_id,
                    plan_code=sessao.plan_code,
                    price_cents=sessao.price_cents,
                    interval=sessao.interval,
                )

        if event.external_id:
            assinatura = (
                session.query(SubscriptionDb)
                .filter(SubscriptionDb.external_id == event.external_id)
                .first()
            )
            if assinatura is not None:
                return _Subject(
                    user_id=assinatura.user_id,
                    plan_code=assinatura.plan_code,
                    price_cents=assinatura.price_cents,
                    interval=assinatura.interval,
                )

    raise UnresolvedSubjectError(
        "Evento não corresponde a nenhuma sessão de checkout nem a assinatura "
        "conhecida; não há a quem conceder."
    )


def handle_event(event: WebhookEvent) -> dict:
    nome = provider().name

    if subscription_service.already_processed(nome, event.id):
        logger.info("Evento %s de %s já processado; ignorando reenvio.", event.id, nome)
        return {"applied": False, "reason": "already_processed"}

    titular = _resolve_subject(event)

    if event.type in ("checkout.completed", "subscription.created", "subscription.renewed"):
        offer = OFFERS_BY_CODE.get(titular.plan_code)
        subscription_service.grant(
            user_id=titular.user_id,
            plan_code=titular.plan_code,
            price_cents=titular.price_cents or (offer.price_cents if offer else 0),
            interval=titular.interval,
            provider=nome,
            external_id=event.external_id,
            period_end=event.period_end,
            locked=bool(offer and offer.founder),
        )
        if event.type == "checkout.completed":
            event_store.record(
                titular.user_id,
                "checkout_completed",
                {"plan": titular.plan_code},
                platform="server",
            )
        aplicado = "granted"

    elif event.type in ("subscription.cancelled", "subscription.expired"):
        subscription_service.cancel(titular.user_id, reason=event.reason)
        aplicado = "cancelled"

    elif event.type == "refund.requested":
        event_store.record(
            titular.user_id,
            "refund_requested",
            {"reason": event.reason or "none"},
            platform="server",
        )
        aplicado = "refund_recorded"

    else:
        logger.info("Evento %s de tipo desconhecido (%s); ignorado.", event.id, event.type)
        aplicado = "ignored"

    subscription_service.mark_processed(nome, event.id, f"{event.type} → {aplicado}")
    return {"applied": True, "effect": aplicado}


@dataclass
class Divergence:
    user_id: str
    reason: str
    gateway: str = ""
    local: str = ""

    def as_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "reason": self.reason,
            "gateway": self.gateway,
            "local": self.local,
        }


def reconcile(now: float | None = None) -> dict:
    moment = now if now is not None else time.time()

    no_gateway = {row["user_id"]: row for row in provider().active_subscriptions()}

    with db_session() as session:
        locais = {row.user_id: row.status for row in session.query(SubscriptionDb).all()}

    divergencias: list[Divergence] = []

    for user_id in no_gateway:
        local = locais.get(user_id)
        if local != "active":
            divergencias.append(
                Divergence(
                    user_id=user_id,
                    reason="pago_sem_direito",
                    gateway="active",
                    local=local or "sem assinatura",
                )
            )

    for user_id, status in locais.items():
        if status == "active" and user_id not in no_gateway:
            divergencias.append(
                Divergence(
                    user_id=user_id,
                    reason="direito_sem_pagamento",
                    gateway="ausente",
                    local=status,
                )
            )

    if divergencias:
        logger.warning("Reconciliação encontrou %d divergência(s).", len(divergencias))

    return {
        "checked_at": moment,
        "gateway_active": len(no_gateway),
        "local_active": sum(1 for s in locais.values() if s == "active"),
        "divergences": [d.as_dict() for d in divergencias],
        "in_sync": not divergencias,
    }
