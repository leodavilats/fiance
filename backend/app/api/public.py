from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app import affirmation
from app.core.ratelimit import ip_rate_limit
from app.models import AffirmationMode, AssetAnalysis
from app.services import AssetService

router = APIRouter()

asset_service = AssetService()

PUBLIC_PER_MINUTE = 60


async def _ip_rate_limit(request: Request, cost: int = 1) -> None:
    await ip_rate_limit(request, "public", PUBLIC_PER_MINUTE, cost=cost)


@router.get("/public/asset/{symbol}", response_model=AssetAnalysis)
async def public_asset(symbol: str, request: Request) -> AssetAnalysis:
    await _ip_rate_limit(request)

    try:
        return await asset_service.analyze_asset(symbol, personalized=False)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/public/affirmation", response_model=AffirmationMode)
async def public_affirmation(request: Request) -> AffirmationMode:
    await _ip_rate_limit(request)

    return AffirmationMode(**affirmation.current().as_dict())
