from __future__ import annotations

from app.core import usage

from .plans import Feature

LIFETIME_WINDOW = "lifetime"

MONTHLY_TTL = usage.DAY * 62
LIFETIME_TTL = usage.DAY * 3650


def _resource(feature: Feature) -> str:
    return f"feature:{feature.value}"


def _window(monthly: bool) -> str:
    return usage.month_window() if monthly else LIFETIME_WINDOW


def used(user_id: str, feature: Feature, monthly: bool = True) -> int:
    return usage.current(user_id, _resource(feature), _window(monthly))


def consume(user_id: str, feature: Feature, amount: int = 1, monthly: bool = True) -> int:
    return usage.increment(
        user_id,
        _resource(feature),
        _window(monthly),
        ttl_seconds=MONTHLY_TTL if monthly else LIFETIME_TTL,
        amount=amount,
    )


def release(user_id: str, feature: Feature, amount: int = 1) -> int:
    atual = used(user_id, feature, monthly=False)
    if atual <= 0:
        return 0
    return consume(user_id, feature, amount=-min(amount, atual), monthly=False)


def reset(user_id: str, feature: Feature, monthly: bool = True) -> int:
    return usage.reset(user_id, _resource(feature), _window(monthly))
