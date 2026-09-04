from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request

from app.core.auth import get_current_user
from app.core.database import outside_request_transaction
from app.storage import event_store

from .plans import Feature
from .resolve import Decision, check


class PaymentRequired(HTTPException):
    def __init__(self, decision: Decision):
        super().__init__(status_code=402, detail=decision.as_dict())


def _record_limit_event(user_id: str, decision: Decision, origin: str) -> None:
    try:
        with outside_request_transaction():
            event_store.record(
                user_id,
                "limit_reached" if decision.limit_reached else "paywall_viewed",
                {"feature": decision.feature.value, "plan": decision.plan.value, "origin": origin},
                platform="server",
            )
    except Exception:
        pass


def requires(feature: Feature, cost: int = 1) -> Callable:

    async def _guard(request: Request, user_id: str = Depends(get_current_user)) -> Decision:
        decision = check(feature, user_id, cost=cost)
        if not decision.allowed:
            _record_limit_event(user_id, decision, origin=request.url.path)
            raise PaymentRequired(decision)
        return decision

    return _guard


def peek(feature: Feature) -> Callable:

    async def _peek(user_id: str = Depends(get_current_user)) -> Decision:
        return check(feature, user_id, cost=0)

    return _peek


def requires_asset_page() -> Callable:

    async def _guard(
        symbol: str,
        request: Request,
        user_id: str = Depends(get_current_user),
    ) -> Decision:
        from app.storage import portfolio_store

        alvo = symbol.strip().upper()
        na_carteira = any(
            item["ticker"].upper() == alvo for item in portfolio_store.list_positions(user_id)
        )

        decision = check(Feature.ASSET_PAGE, user_id, cost=0 if na_carteira else 1)
        if not decision.allowed:
            _record_limit_event(user_id, decision, origin=request.url.path)
            raise PaymentRequired(decision)
        return decision

    return _guard
