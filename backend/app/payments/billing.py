"""Cobrança: catálogo de preço, checkout, webhook e reconciliação.

Quatro coisas, e a ordem delas é a ordem em que o dinheiro se perde quando
alguma falha:

* **Catálogo** — o preço de tabela. Quem já assinou não é alcançado por
  mudanças aqui; a assinatura carrega o próprio preço.
* **Checkout** — cria a sessão no provedor. Não concede nada: conceder no
  checkout daria Premium a quem abandonou o pagamento.
* **Webhook** — concede. Idempotente por id de evento, porque o provedor
  reenvia até receber 200 e conceder duas vezes é o modo de falha óbvio.
* **Reconciliação** — compara o que o gateway diz estar ativo com o que foi
  concedido. Webhook perdido é silencioso dos dois lados: ninguém reclama de
  ter pago e não ter recebido até tentar usar.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from app.core.config import get_settings
from app.core.database import db_session
from app.models.db_models import SubscriptionDb
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
    #: Quanto sai por mês, para a comparação que o usuário faz de cabeça.
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


#: O catálogo. O anual em destaque e o mensal sem fricção — desconto de ~25%
#: bate a âncora do mercado e quebra a barreira dos R$ 15 sem sinalizar que o
#: preço cheio é falso.
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
    """O provedor em uso.

    Enquanto não houver chave da Stripe, é o falso — e ele é o provedor de
    desenvolvimento, não um andaime de teste. Trocar por Stripe é substituir
    esta função, não reescrever o fluxo.
    """
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
    """Código de plano que não existe no catálogo."""


def start_checkout(user_id: str, plan_code: str) -> dict:
    """Cria a sessão. **Não concede nada.**

    Conceder aqui daria Premium a quem abriu o checkout e desistiu — e é um
    erro que só aparece na conciliação do mês seguinte.
    """
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


def handle_event(event: WebhookEvent) -> dict:
    """Aplica o efeito de um evento do gateway. Idempotente.

    A marca de processado é gravada **depois** do efeito: marcar antes e falhar
    no meio perderia a concessão para sempre, porque a retentativa do provedor
    encontraria o evento já marcado.
    """
    nome = provider().name

    if subscription_service.already_processed(nome, event.id):
        logger.info("Evento %s de %s já processado; ignorando reenvio.", event.id, nome)
        return {"applied": False, "reason": "already_processed"}

    if not event.user_id:
        raise ValueError("Evento sem usuário; não há a quem conceder.")

    if event.type in ("checkout.completed", "subscription.created", "subscription.renewed"):
        offer = OFFERS_BY_CODE.get(event.plan_code)
        subscription_service.grant(
            user_id=event.user_id,
            plan_code=event.plan_code,
            # O preço vem do **evento**, não da tabela vigente: é o que a
            # pessoa efetivamente contratou, e é o que a promessa de preço
            # travado precisa preservar.
            price_cents=event.price_cents or (offer.price_cents if offer else 0),
            interval=event.interval,
            provider=nome,
            external_id=event.external_id,
            period_end=event.period_end,
            locked=bool(offer and offer.founder),
        )
        if event.type == "checkout.completed":
            event_store.record(
                event.user_id, "checkout_completed", {"plan": event.plan_code}, platform="server"
            )
        aplicado = "granted"

    elif event.type in ("subscription.cancelled", "subscription.expired"):
        subscription_service.cancel(event.user_id, reason=event.reason)
        aplicado = "cancelled"

    elif event.type == "refund.requested":
        event_store.record(
            event.user_id,
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
    """Compara o gateway com os direitos concedidos.

    Webhook perdido é silencioso dos dois lados: o gateway acha que entregou, o
    produto nunca soube, e o usuário só descobre quando tenta usar. Uma rotina
    diária é a diferença entre descobrir isso em horas e descobrir por
    reclamação.
    """
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
