from __future__ import annotations

import asyncio
import base64

from fastapi import APIRouter, HTTPException, Request, Response

from app import affirmation
from app.core import cache
from app.core.brt import now_brt
from app.core.ratelimit import ip_rate_limit
from app.core.universe import get_universe
from app.models import (
    AffirmationMode,
    AssetAnalysis,
    InterestSignupRequest,
    InterestSignupResponse,
)
from app.services import AssetService, og_image
from app.storage import interest_store

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


OG_TTL = 6 * 3600


@router.get(
    "/public/asset/{symbol}/og.png",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}, "description": "PNG de 1200×630."}},
)
async def public_asset_og(symbol: str, request: Request) -> Response:
    await ip_rate_limit(request, "public-og", PUBLIC_PER_MINUTE)

    alvo = symbol.strip().upper()
    chave = f"og:asset:{alvo}"

    guardada = cache.get(chave)
    if guardada:
        return Response(
            content=base64.b64decode(guardada),
            media_type="image/png",
            headers={"Cache-Control": f"public, max-age={OG_TTL}"},
        )

    try:
        analise = await asset_service.analyze_asset(alvo, personalized=False)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc

    png = await asyncio.to_thread(
        og_image.render,
        analise.symbol,
        analise.name,
        analise.decision.verdict,
        analise.decision.label,
        analise.price,
        analise.fair_price.consensus if analise.fair_price else None,
    )

    cache.set(chave, base64.b64encode(png).decode(), OG_TTL)

    return Response(
        content=png,
        media_type="image/png",
        headers={"Cache-Control": f"public, max-age={OG_TTL}"},
    )


@router.get("/public/universe")
async def public_universe(request: Request) -> dict:
    await _ip_rate_limit(request, cost=2)

    tickers = await asyncio.to_thread(get_universe)
    return {
        "tickers": tickers,
        "count": len(tickers),
        "lastmod": now_brt().strftime("%Y-%m-%d"),
    }


@router.get("/public/affirmation", response_model=AffirmationMode)
async def public_affirmation(request: Request) -> AffirmationMode:
    await _ip_rate_limit(request)

    return AffirmationMode(**affirmation.current().as_dict())


@router.post("/public/interest", response_model=InterestSignupResponse)
async def register_interest(
    body: InterestSignupRequest, request: Request
) -> InterestSignupResponse:
    await ip_rate_limit(request, "interest", 5)

    return InterestSignupResponse(registered=interest_store.register(body.email, body.source))
