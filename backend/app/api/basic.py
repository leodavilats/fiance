import asyncio
import logging

from fastapi import APIRouter, Response
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.collectors import circuit
from app.core import cache
from app.core.database import SessionLocal
from app.core.observability import metrics
from app.core.universe import get_universe, invalidate_universe_memo, search_universe

logger = logging.getLogger("fiance.health")

router = APIRouter()

admin_router = APIRouter()


class HealthResponse(BaseModel):
    status: str


class CheckResult(BaseModel):
    ok: bool
    detail: str = ""


class ReadyResponse(BaseModel):
    ready: bool
    checks: dict[str, CheckResult]
    sources: dict[str, str] = Field(
        default_factory=dict,
        description="Estado do disjuntor de cada fonte: fechado | meia-abertura | aberto.",
    )


@router.get("/health", response_model=HealthResponse)
async def health() -> dict:
    return {"status": "ok"}


def _checar_banco() -> tuple[bool, str]:
    session = SessionLocal()
    try:
        session.execute(text("SELECT 1"))
        return True, "ok"
    except Exception as exc:
        logger.warning("Readiness: banco inacessível (%s).", exc)
        return False, str(exc)[:200]
    finally:
        session.close()


def _checar_cache() -> tuple[bool, str]:
    try:
        cache.set("health:probe", 1, 30)
        return cache.get("health:probe") == 1, "ok"
    except Exception as exc:
        logger.warning("Readiness: cache inacessível (%s).", exc)
        return False, str(exc)[:200]


@router.get("/ready", response_model=ReadyResponse)
async def ready(response: Response) -> dict:
    banco_ok, banco_detalhe = await asyncio.to_thread(_checar_banco)
    cache_ok, cache_detalhe = await asyncio.to_thread(_checar_cache)

    pronto = banco_ok and cache_ok
    if not pronto:
        response.status_code = 503

    return {
        "ready": pronto,
        "checks": {
            "database": {"ok": banco_ok, "detail": banco_detalhe},
            "cache": {"ok": cache_ok, "detail": cache_detalhe},
        },
        "sources": {nome: circuit.status(nome)["state"] for nome in ("brapi", "bcb", "ibov")},
    }


@router.get("/universe")
async def universe() -> dict:
    return {"tickers": await asyncio.to_thread(get_universe)}


@router.get("/universe/search")
async def universe_search(q: str = "", limit: int = 10) -> dict:
    limit = max(1, min(limit, 25))
    return {"items": await asyncio.to_thread(search_universe, q, limit)}


@admin_router.post("/cache/clear")
async def clear_cache(pattern: str = "*") -> dict:
    invalidate_universe_memo()

    if pattern == "*":
        count = cache.clear_all()
        return {"message": "Cache totalmente limpo", "deleted": count}

    sql_pattern = pattern.replace("*", "%")
    count = cache.delete_pattern(sql_pattern)
    return {"message": f"Cache limpo para padrão: {pattern}", "deleted": count}


@admin_router.get("/metrics")
async def read_metrics() -> dict:
    return {**metrics.snapshot(), "cache": cache.describe()}


@admin_router.post("/metrics/reset")
async def reset_metrics() -> dict:
    metrics.reset()
    return {"reset": True}
