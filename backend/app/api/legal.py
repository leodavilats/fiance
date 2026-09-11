from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.core.ratelimit import ip_rate_limit
from app.services import legal_pages

router = APIRouter()

LEGAL_PER_MINUTE = 60
CACHE = "public, max-age=3600"


async def _html(request: Request, corpo: str) -> Response:
    await ip_rate_limit(request, "legal", LEGAL_PER_MINUTE)

    return Response(
        content=corpo,
        media_type="text/html; charset=utf-8",
        headers={
            "Cache-Control": CACHE,
        },
    )


@router.get("/termos", include_in_schema=False)
async def termos(request: Request) -> Response:
    return await _html(request, legal_pages.termos())


@router.get("/privacidade", include_in_schema=False)
async def privacidade(request: Request) -> Response:
    return await _html(request, legal_pages.privacidade())


@router.get("/aviso-cvm", include_in_schema=False)
async def aviso_cvm(request: Request) -> Response:
    return await _html(request, legal_pages.aviso_cvm())
