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
    pass


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
        return [
            {"user_id": uid, **dados}
            for uid, dados in self.granted.items()
            if dados.get("status") == "active"
        ]
