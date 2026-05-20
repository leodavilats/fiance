"""Controller para oportunidades de investimento."""

from fastapi import APIRouter, Query

from app.models import OpportunitiesResponse
from app.services import OpportunityService

router = APIRouter()

opportunity_service = OpportunityService()


@router.get("/opportunities", response_model=OpportunitiesResponse)
async def opportunities(
    include_held: bool = Query(False, description="Inclui ativos já em carteira"),
    only_buy: bool = Query(True, description="Apenas BUY e STRONG_BUY"),
    page: int = Query(1, ge=1, description="Página atual (começa em 1)"),
    page_size: int = Query(50, ge=10, le=100, description="Itens por página"),
    sort_by: str = Query("score", description="Campo para ordenação: score, dy, mos, price"),
    sort_order: str = Query("desc", description="Ordem: asc ou desc"),
) -> OpportunitiesResponse:
    """Retorna lista de oportunidades de investimento."""
    return await opportunity_service.get_opportunities(
        include_held, only_buy, page, page_size, sort_by, sort_order
    )
