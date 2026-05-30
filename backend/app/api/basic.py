from fastapi import APIRouter

from app.core import cache
from app.core.config import get_settings

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/universe")
async def universe() -> dict:
    return {"tickers": get_settings().universe}


@router.post("/cache/clear")
async def clear_cache(pattern: str = "*") -> dict:
    """Limpa cache. Use pattern='uasset:*' para limpar apenas ativos."""
    if pattern == "*":
        count = cache.clear_all()
        return {"message": "Cache totalmente limpo", "deleted": count}

    # Converte pattern shell-style para SQL LIKE
    sql_pattern = pattern.replace("*", "%")
    count = cache.delete_pattern(sql_pattern)
    return {"message": f"Cache limpo para padrão: {pattern}", "deleted": count}
