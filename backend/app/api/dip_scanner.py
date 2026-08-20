from fastapi import APIRouter, Query

from app.models import DipScannerResponse
from app.services import DipService

router = APIRouter()

dip_service = DipService()


@router.get("/dip-scanner", response_model=DipScannerResponse)
async def dip_scanner(
    universe: str | None = Query(
        None, description="Tickers separados por vírgula. Padrão: universo do sistema"
    ),
    min_score: float = Query(
        40.0, ge=0, le=100, description="Score mínimo para incluir no resultado"
    ),
    top: int = Query(12, ge=1, le=30, description="Máximo de itens retornados"),
    category: str | None = Query(
        None, description="Filtrar por categoria: acoes_br | bdrs | fiis | etfs"
    ),
) -> DipScannerResponse:
    # A categoria precisa filtrar antes do corte de `top`: filtrar depois
    # devolvia "o que sobrou dos 12 maiores dips do universo inteiro" em vez
    # dos 12 maiores dips da categoria pedida.
    return await dip_service.scan_dips(universe, min_score, top, category=category)
