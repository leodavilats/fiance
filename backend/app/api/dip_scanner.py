"""Controller para scanner de dips."""

from typing import Optional

from fastapi import APIRouter, Query

from app.models import DipScannerResponse
from app.services import DipService

router = APIRouter()

dip_service = DipService()


@router.get("/dip-scanner", response_model=DipScannerResponse)
async def dip_scanner(
    universe: Optional[str] = Query(None, description="Tickers separados por vírgula. Padrão: universo + watchlist"),
    min_score: float = Query(40.0, ge=0, le=100, description="Score mínimo para incluir no resultado"),
    top: int = Query(12, ge=1, le=30, description="Máximo de itens retornados"),
    desired_yield: float = Query(0.06, gt=0, le=0.30, description="Yield desejado para cálculo Bazin"),
) -> DipScannerResponse:
    """Escaneia o universo em busca de oportunidades de dip."""
    return await dip_service.scan_dips(universe, min_score, top, desired_yield)
