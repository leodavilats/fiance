from fastapi import APIRouter, HTTPException

from app.models import AssetAnalysis, DipAnalysisResponse
from app.services import AssetService, DipService

router = APIRouter()

asset_service = AssetService()
dip_service = DipService()


@router.get("/asset/{symbol}", response_model=AssetAnalysis)
async def analyze_asset(
    symbol: str,
) -> AssetAnalysis:
    try:
        return await asset_service.analyze_asset(symbol)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get("/asset/{symbol}/dip-analysis", response_model=DipAnalysisResponse)
async def dip_analysis(
    symbol: str,
) -> DipAnalysisResponse:
    try:
        return await dip_service.analyze_dip(symbol)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
