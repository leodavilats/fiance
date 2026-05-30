"""Controller para scanner de dips."""

from fastapi import APIRouter, Query

from app.models import DipScannerResponse
from app.services import DipService

router = APIRouter()

dip_service = DipService()


@router.get("/dip-scanner", response_model=DipScannerResponse)
async def dip_scanner(
    universe: str | None = Query(
        None, description="Tickers separados por vírgula. Padrão: universo + watchlist"
    ),
    min_score: float = Query(
        40.0, ge=0, le=100, description="Score mínimo para incluir no resultado"
    ),
    top: int = Query(12, ge=1, le=30, description="Máximo de itens retornados"),
    desired_yield: float = Query(
        0.06, gt=0, le=0.30, description="Yield desejado para cálculo Bazin"
    ),
    category: str | None = Query(
        None, description="Filtrar por categoria: acoes_br | acoes_int | fiis | cripto"
    ),
) -> DipScannerResponse:
    """Escaneia o universo em busca de oportunidades de dip."""
    result = await dip_service.scan_dips(universe, min_score, top, desired_yield)

    if category:
        from app.analysis.classify import auto_category

        result.items = [
            item
            for item in result.items
            if auto_category(
                item.asset_type.value
                if hasattr(item.asset_type, "value")
                else str(item.asset_type),
                None,
            )
            == category
        ]

    return result
