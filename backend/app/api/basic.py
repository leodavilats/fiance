import asyncio

from fastapi import APIRouter

from app.core import cache
from app.core.universe import get_universe, search_universe

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/universe")
async def universe() -> dict:
    return {"tickers": await asyncio.to_thread(get_universe)}


@router.get("/universe/search")
async def universe_search(q: str = "", limit: int = 10) -> dict:
    """Autocomplete de ticker (web/mobile) — busca por prefixo/substring em
    ticker ou nome da empresa, em todo o universo (não só o curado)."""
    limit = max(1, min(limit, 25))
    return {"items": await asyncio.to_thread(search_universe, q, limit)}


@router.post("/cache/clear")
async def clear_cache(pattern: str = "*") -> dict:
    if pattern == "*":
        count = cache.clear_all()
        return {"message": "Cache totalmente limpo", "deleted": count}

    sql_pattern = pattern.replace("*", "%")
    count = cache.delete_pattern(sql_pattern)
    return {"message": f"Cache limpo para padrão: {pattern}", "deleted": count}
