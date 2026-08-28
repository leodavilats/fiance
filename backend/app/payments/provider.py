"""O contrato do gateway, e o gateway falso que o exercita.

O direito mora no backend ligado ao `user_id`; o gateway é **detalhe de canal**.
Essa não é uma afirmação de arquitetura bonita: é o que permite vender na web
(1,19% no Pix, 3,99% no cartão) e liberar no app sem migrar assinante quando a
compra in-app entrar — 14 pontos de diferença sobre R$ 179,90, que em mil
assinantes anuais são ~R$ 25 mil por ano.

Por isso o provedor é uma interface. O falso não é andaime de teste: é o
provedor de desenvolvimento, e é ele que roda enquanto não houver conta. A
integração real com a Stripe **não é verificável sem chave** — o que este
módulo garante é que o contrato à volta dela esteja certo: sessão criada,
webhook idempotente, assinatura verificada, reconciliação possível.
"""

from __future__ import annotations

import hashlib
import hmac
import time
import uuid
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class CheckoutSession:
    id: str
    url: str
    provider: str
    expires_at: float


@dataclass(frozen=True)
class WebhookEvent:
    """Um evento normalizado, já traduzido do vocabulário do provedor."""

    id: str
    type: str
    user_id: str
    plan_code: str = "premium"
    price_cents: int = 0
    interval: str = "monthly"
    external_id: str | None = None
    period_end: float | None = None
    reason: str = ""


class SignatureError(ValueError):
    """Assinatura de webhook inválida — a requisição não veio do provedor."""


class PaymentProvider(Protocol):
    name: str

    def create_checkout(
        self, user_id: str, plan_code: str, price_cents: int, interval: str
    ) -> CheckoutSession: ...

    def verify(self, payload: bytes, signature: str) -> None: ...

    def parse(self, payload: dict) -> WebhookEvent: ...

    def active_subscriptions(self) -> list[dict]: ...


@dataclass
class FakeProvider:
    """Provedor de desenvolvimento. Assina com HMAC como a Stripe faz.

    Assinar de verdade importa: um falso que aceitasse qualquer requisição
    deixaria o caminho de verificação sem exercício nenhum, e é justamente ele
    que não pode estar errado — webhook sem verificação de assinatura é uma
    rota pública que concede assinatura.
    """

    name: str = "fake"
    secret: str = "segredo-de-desenvolvimento"
    sessions: dict[str, dict] = field(default_factory=dict)
    granted: dict[str, dict] = field(default_factory=dict)

    def create_checkout(
        self, user_id: str, plan_code: str, price_cents: int, interval: str
    ) -> CheckoutSession:
        session_id = f"cs_fake_{uuid.uuid4().hex[:16]}"
        self.sessions[session_id] = {
            "user_id": user_id,
            "plan_code": plan_code,
            "price_cents": price_cents,
            "interval": interval,
        }
        return CheckoutSession(
            id=session_id,
            url=f"https://checkout.local/{session_id}",
            provider=self.name,
            expires_at=time.time() + 3600,
        )

    def sign(self, payload: bytes) -> str:
        return hmac.new(self.secret.encode(), payload, hashlib.sha256).hexdigest()

    def verify(self, payload: bytes, signature: str) -> None:
        esperado = self.sign(payload)
        # Comparação em tempo constante: comparar com `==` vaza o prefixo
        # correto pelo tempo de resposta, e o atacante precisa de um oráculo
        # só para forjar a assinatura byte a byte.
        if not hmac.compare_digest(esperado, signature or ""):
            raise SignatureError("Assinatura do webhook não confere.")

    def parse(self, payload: dict) -> WebhookEvent:
        return WebhookEvent(
            id=str(payload.get("id") or ""),
            type=str(payload.get("type") or ""),
            user_id=str(payload.get("user_id") or ""),
            plan_code=str(payload.get("plan_code") or "premium"),
            price_cents=int(payload.get("price_cents") or 0),
            interval=str(payload.get("interval") or "monthly"),
            external_id=payload.get("external_id"),
            period_end=payload.get("period_end"),
            reason=str(payload.get("reason") or ""),
        )

    def active_subscriptions(self) -> list[dict]:
        """O que o gateway considera ativo — a fonte da reconciliação."""
        return [
            {"user_id": uid, **dados}
            for uid, dados in self.granted.items()
            if dados.get("status") == "active"
        ]
