"""Controller para ranking de dividendos."""

from typing import Optional

from fastapi import APIRouter, Query

from app.models import DividendRankingResponse
from app.services import DividendService

router = APIRouter()

dividend_service = DividendService()


@router.get("/dividends/ranking", response_model=DividendRankingResponse)
async def dividends_ranking(
    universe: Optional[str] = Query(
        None, description="Tickers separados por vírgula. Usa default se omitido."
    ),
    top: int = Query(15, ge=1, le=50),
) -> DividendRankingResponse:
    """Retorna ranking de ativos por dividend yield."""
    return await dividend_service.get_dividend_ranking(universe, top)
