import asyncio

from fastapi import APIRouter

from app.core import cache
from app.core.observability import metrics
from app.core.universe import get_universe, invalidate_universe_memo, search_universe

router = APIRouter()

# Endpoints de manutenção: incluídos no router protegido em app/api/__init__.py.
# Deixar /cache/clear público permitia a qualquer um apagar o universo e o scan
# completo em loop, travando o dashboard de todos e queimando cota da BRAPI.
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
    # Os índices memoizados em processo derivam do cache; limpar um sem o outro
    # deixaria setor/autocomplete servindo dado velho.
    invalidate_universe_memo()

    if pattern == "*":
        count = cache.clear_all()
        return {"message": "Cache totalmente limpo", "deleted": count}

    sql_pattern = pattern.replace("*", "%")
    count = cache.delete_pattern(sql_pattern)
    return {"message": f"Cache limpo para padrão: {pattern}", "deleted": count}


@admin_router.get("/metrics")
async def read_metrics() -> dict:
    """Contadores em processo: chamadas externas, cache hit rate, latência.

    Não havia observabilidade alguma — nem métrica, nem tracing, nem ID de
    correlação. Sem isso não há como saber qual endpoint está lento em produção
    nem quanto da cota da BRAPI está sendo gasta.
    """
    return metrics.snapshot()


@admin_router.post("/metrics/reset")
async def reset_metrics() -> dict:
    metrics.reset()
    return {"reset": True}
