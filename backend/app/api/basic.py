import asyncio

from fastapi import APIRouter

from app.core import cache
from app.core.observability import metrics
from app.core.universe import get_universe, invalidate_universe_memo, search_universe

router = APIRouter()

admin_router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


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
