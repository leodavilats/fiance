from fastapi import APIRouter, HTTPException

from app.models import (
    ClosedTrade,
    ClosedTradesResponse,
    PortfolioEvaluationRequest,
    PortfolioEvaluationResponse,
    PortfolioStateResponse,
    SavePortfolioRequest,
    SellRequest,
)
from app.services import PortfolioService

router = APIRouter()

portfolio_service = PortfolioService()


@router.post("/portfolio/evaluate", response_model=PortfolioEvaluationResponse)
async def evaluate_portfolio(req: PortfolioEvaluationRequest) -> PortfolioEvaluationResponse:
    try:
        return await portfolio_service.evaluate_portfolio(req)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/portfolio", response_model=PortfolioStateResponse)
async def get_portfolio() -> PortfolioStateResponse:
    return portfolio_service.get_portfolio()


@router.put("/portfolio", response_model=PortfolioStateResponse)
async def save_portfolio(req: SavePortfolioRequest) -> PortfolioStateResponse:
    return portfolio_service.save_portfolio(req)


@router.delete("/portfolio/{ticker}")
async def delete_position(ticker: str) -> dict:
    return portfolio_service.delete_position(ticker)


@router.post("/portfolio/sell", response_model=ClosedTrade)
async def sell_position(req: SellRequest) -> ClosedTrade:
    try:
        return await portfolio_service.sell_position(req)
    except ValueError as e:
        status = 404 if "não encontrada" in str(e) else 400
        raise HTTPException(status, str(e)) from e


@router.get("/portfolio/trades", response_model=ClosedTradesResponse)
async def get_closed_trades() -> ClosedTradesResponse:
    return portfolio_service.get_closed_trades()
