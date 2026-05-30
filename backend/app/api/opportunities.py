"""Controller para oportunidades de investimento."""

from fastapi import APIRouter, Query

from app.models import OpportunitiesResponse
from app.services import OpportunityService

router = APIRouter()

opportunity_service = OpportunityService()


@router.get("/opportunities", response_model=OpportunitiesResponse)
async def opportunities(
    include_held: bool = Query(False, description="Inclui ativos já em carteira"),
    page: int = Query(1, ge=1, description="Página atual (começa em 1)"),
    page_size: int = Query(50, ge=10, le=100, description="Itens por página"),
    sort_by: str = Query("score", description="Campo para ordenação: score, dy, mos, price"),
    sort_order: str = Query("desc", description="Ordem: asc ou desc"),
    search: str = Query("", description="Busca por ticker ou nome"),
    min_dy: float = Query(0, ge=0, description="DY mínimo (%)"),
    min_mos: float = Query(0, description="MS mínima (%)"),
    sector: str = Query("", description="Filtrar por setor"),
    asset_type: str = Query("", description="Filtrar por tipo de ativo"),
    category: str = Query("", description="Filtrar por categoria: renda ou trade"),
    only_interesting: bool = Query(False, description="Apenas destaques"),
) -> OpportunitiesResponse:
    """Retorna lista de oportunidades de investimento."""
    return await opportunity_service.get_opportunities(
        include_held=include_held,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
        min_dy=min_dy,
        min_mos=min_mos,
        sector=sector,
        asset_type=asset_type,
        category=category,
        only_interesting=only_interesting,
    )
