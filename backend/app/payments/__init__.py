"""Cobrança: o contrato do gateway e o que se faz com os eventos dele.

O direito mora no backend ligado ao `user_id`; o gateway é detalhe de canal.
É isso que permite vender na web e liberar no app sem migrar assinante quando a
compra in-app entrar — 14 pontos de diferença de taxa entre os dois.
"""

from .billing import (
    OFFERS,
    Divergence,
    PlanOffer,
    UnknownPlanError,
    handle_event,
    offers,
    provider,
    reconcile,
    set_provider,
    start_checkout,
)
from .provider import (
    CheckoutSession,
    FakeProvider,
    PaymentProvider,
    SignatureError,
    WebhookEvent,
)

__all__ = [
    "OFFERS",
    "CheckoutSession",
    "Divergence",
    "FakeProvider",
    "PaymentProvider",
    "PlanOffer",
    "SignatureError",
    "UnknownPlanError",
    "WebhookEvent",
    "handle_event",
    "offers",
    "provider",
    "reconcile",
    "set_provider",
    "start_checkout",
]
