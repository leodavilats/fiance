from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.core.config import get_settings
from app.core.database import db_session
from app.models.db_models import SubscriptionDb

from . import meter
from .plans import Feature, Plan, allows, limit_for, rule_for

TRIAL_DAYS = 14

ACTIVE_STATUSES = frozenset({"active", "past_due"})


@dataclass
class Entitlements:
    plan: Plan
    unrestricted: bool = False
    trial_ends_at: float | None = None
    in_trial: bool = False
    credited_until: float | None = None
    price_cents: int = 0
    locked_price: bool = False
    features: dict[str, bool] = field(default_factory=dict)
    limits: dict[str, int | None] = field(default_factory=dict)

    @property
    def days_left_in_trial(self) -> int | None:
        if not self.in_trial or self.trial_ends_at is None:
            return None
        return max(0, int((self.trial_ends_at - time.time()) // 86400))

    def as_dict(self) -> dict:
        return {
            "plan": self.plan.value,
            "unrestricted": self.unrestricted,
            "in_trial": self.in_trial,
            "trial_ends_at": self.trial_ends_at,
            "trial_days_left": self.days_left_in_trial,
            "credited_until": self.credited_until,
            "price_cents": self.price_cents,
            "locked_price": self.locked_price,
            "features": dict(self.features),
            "limits": dict(self.limits),
        }


@dataclass(frozen=True)
class _Snapshot:
    status: str
    trial_ends_at: float | None
    credited_until: float | None
    current_period_end: float | None
    price_cents: int
    locked: bool


def _subscription(user_id: str) -> _Snapshot | None:
    with db_session() as session:
        row = session.get(SubscriptionDb, user_id)
        if row is None:
            return None
        return _Snapshot(
            status=row.status,
            trial_ends_at=row.trial_ends_at,
            credited_until=row.credited_until,
            current_period_end=row.current_period_end,
            price_cents=row.price_cents,
            locked=bool(row.locked),
        )


def resolve(user_id: str, now: float | None = None) -> Entitlements:
    moment = now if now is not None else time.time()
    settings = get_settings()

    if not settings.entitlements_enabled:
        return Entitlements(
            plan=Plan.PREMIUM,
            unrestricted=True,
            features={f.value: True for f in Feature},
            limits={f.value: None for f in Feature},
        )

    row = _subscription(user_id)
    plan = Plan.FREE
    in_trial = False
    trial_ends_at = None
    credited_until = None
    price_cents = 0
    locked = False

    if row is not None:
        trial_ends_at = row.trial_ends_at
        credited_until = row.credited_until
        price_cents = row.price_cents
        locked = row.locked

        in_trial = trial_ends_at is not None and moment < trial_ends_at

        assinatura_vale = row.status in ACTIVE_STATUSES and (
            row.current_period_end is None or moment < row.current_period_end
        )

        com_credito = row.credited_until is not None and moment < row.credited_until

        if assinatura_vale or in_trial or com_credito:
            plan = Plan.PREMIUM

    features = {f.value: allows(f, plan) for f in Feature}
    limits = {f.value: limit_for(f, plan) for f in Feature}

    return Entitlements(
        plan=plan,
        trial_ends_at=trial_ends_at,
        in_trial=in_trial,
        credited_until=credited_until,
        price_cents=price_cents,
        locked_price=locked,
        features=features,
        limits=limits,
    )


@dataclass
class Decision:
    allowed: bool
    feature: Feature
    plan: Plan
    reason: str = ""
    limit: int | None = None
    used: int = 0
    limit_reached: bool = False

    def as_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "feature": self.feature.value,
            "plan": self.plan.value,
            "required_plan": rule_for(self.feature).min_plan.value,
            "reason": self.reason,
            "limit": self.limit,
            "used": self.used,
            "limit_reached": self.limit_reached,
        }


def check(feature: Feature, user_id: str, cost: int = 0) -> Decision:
    direitos = resolve(user_id)

    if direitos.unrestricted:
        return Decision(True, feature, direitos.plan)

    regra = rule_for(feature)

    if not allows(feature, direitos.plan):
        return Decision(
            allowed=False,
            feature=feature,
            plan=direitos.plan,
            reason=regra.rationale or "Disponível no plano Premium.",
        )

    limite = limit_for(feature, direitos.plan)
    if limite is None:
        if cost:
            meter.consume(user_id, feature, amount=cost, monthly=regra.monthly)
        return Decision(True, feature, direitos.plan, limit=None)

    usado = meter.used(user_id, feature, monthly=regra.monthly)

    if usado + cost > limite:
        return Decision(
            allowed=False,
            feature=feature,
            plan=direitos.plan,
            reason=(f"Você usou {usado} de {limite} {regra.unit} do plano {direitos.plan.value}."),
            limit=limite,
            used=usado,
            limit_reached=True,
        )

    if cost:
        meter.consume(user_id, feature, amount=cost, monthly=regra.monthly)

    return Decision(True, feature, direitos.plan, limit=limite, used=usado + cost)
