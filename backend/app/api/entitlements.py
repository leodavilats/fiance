from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.entitlement import Feature, check, plans, resolve
from app.services import subscription_service

router = APIRouter()


@router.get("/entitlements")
async def read_entitlements(user_id: str = Depends(get_current_user)) -> dict:
    direitos = resolve(user_id)
    assinatura = subscription_service.get(user_id)

    return {
        **direitos.as_dict(),
        "subscription": {
            "status": assinatura["status"],
            "plan_code": assinatura["plan_code"],
            "interval": assinatura["interval"],
            "price_cents": assinatura["price_cents"],
            "locked": assinatura["locked"],
            "current_period_end": assinatura["current_period_end"],
        },
    }


@router.get("/entitlements/rules")
async def read_rules() -> dict:
    return {"rules": plans.as_dicts()}


@router.get("/entitlements/check/{feature}")
async def check_feature(feature: Feature, user_id: str = Depends(get_current_user)) -> dict:
    return check(feature, user_id, cost=0).as_dict()
