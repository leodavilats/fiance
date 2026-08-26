import asyncio

from fastapi import APIRouter, HTTPException, Query

from app.models import AssetAnalysis, CompareResponse, DipAnalysisResponse
from app.services import AssetService, DipService

router = APIRouter()

asset_service = AssetService()
dip_service = DipService()

MAX_COMPARE_TICKERS = 4


@router.get("/asset/{symbol}", response_model=AssetAnalysis)
async def analyze_asset(
    symbol: str,
) -> AssetAnalysis:
    try:
        return await asset_service.analyze_asset(symbol)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get("/compare", response_model=CompareResponse)
async def compare_assets(
    tickers: str = Query(..., description="Tickers separados por vírgula, ex.: PETR4,VALE3"),
) -> CompareResponse:
    symbols = [t.strip().upper() for t in tickers.split(",") if t.strip()][:MAX_COMPARE_TICKERS]
    if not symbols:
        raise HTTPException(400, "Informe ao menos um ticker.")

    results = await asyncio.gather(
        *(asset_service.analyze_asset(s, include_history=False) for s in symbols),
        return_exceptions=True,
    )

    items: list[AssetAnalysis] = []
    errors: list[str] = []
    for symbol, result in zip(symbols, results, strict=True):
        if isinstance(result, AssetAnalysis):
            items.append(result)
        else:
            errors.append(symbol)

    return CompareResponse(items=items, errors=errors)


@router.get("/asset/{symbol}/dip-analysis", response_model=DipAnalysisResponse)
async def dip_analysis(
    symbol: str,
) -> DipAnalysisResponse:
    try:
        return await dip_service.analyze_dip(symbol)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
