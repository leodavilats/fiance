import asyncio

from fastapi import APIRouter

from app.core import cache
from app.core.universe import get_universe

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/universe")
async def universe() -> dict:
    return {"tickers": await asyncio.to_thread(get_universe)}


@router.post("/cache/clear")
async def clear_cache(pattern: str = "*") -> dict:
    if pattern == "*":
        count = cache.clear_all()
        return {"message": "Cache totalmente limpo", "deleted": count}

    sql_pattern = pattern.replace("*", "%")
    count = cache.delete_pattern(sql_pattern)
    return {"message": f"Cache limpo para padrão: {pattern}", "deleted": count}
