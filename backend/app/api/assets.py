"""Controllers para análise de ativos."""

from fastapi import APIRouter, HTTPException, Query

from app.models import AssetAnalysis, DipAnalysisResponse
from app.services import AssetService, DipService

router = APIRouter()

asset_service = AssetService()
dip_service = DipService()


@router.get("/asset/{symbol}", response_model=AssetAnalysis)
async def analyze_asset(
    symbol: str,
    desired_yield: float = Query(0.06, gt=0, le=0.30, description="Yield desejado (Bazin)"),
) -> AssetAnalysis:
    """Analisa um ativo."""
    try:
        return await asset_service.analyze_asset(symbol, desired_yield)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get("/asset/{symbol}/dip-analysis", response_model=DipAnalysisResponse)
async def dip_analysis(
    symbol: str,
    desired_yield: float = Query(0.06, gt=0, le=0.30, description="Yield desejado (Bazin)"),
) -> DipAnalysisResponse:
    """Analisa oportunidade de dip em um ativo."""
    try:
        return await dip_service.analyze_dip(symbol, desired_yield)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
