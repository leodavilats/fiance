"""Controller para operações de portfolio."""

from fastapi import APIRouter, HTTPException

from app.models import (
    PortfolioEvaluationRequest,
    PortfolioEvaluationResponse,
    PortfolioStateResponse,
    SavePortfolioRequest,
)
from app.services import PortfolioService

router = APIRouter()

portfolio_service = PortfolioService()


@router.post("/portfolio/evaluate", response_model=PortfolioEvaluationResponse)
async def evaluate_portfolio(req: PortfolioEvaluationRequest) -> PortfolioEvaluationResponse:
    """Avalia o portfolio."""
    try:
        return await portfolio_service.evaluate_portfolio(req)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/portfolio", response_model=PortfolioStateResponse)
async def get_portfolio() -> PortfolioStateResponse:
    """Retorna o estado atual do portfolio."""
    return portfolio_service.get_portfolio()


@router.put("/portfolio", response_model=PortfolioStateResponse)
async def save_portfolio(req: SavePortfolioRequest) -> PortfolioStateResponse:
    """Salva o portfolio."""
    return portfolio_service.save_portfolio(req)


@router.delete("/portfolio/{ticker}")
async def delete_position(ticker: str) -> dict:
    """Remove uma posição do portfolio."""
    return portfolio_service.delete_position(ticker)


@router.post("/portfolio/refresh", response_model=PortfolioEvaluationResponse)
async def refresh_portfolio(desired_yield: float = 0.06) -> PortfolioEvaluationResponse:
    """Atualiza e reavalia o portfolio."""
    try:
        return await portfolio_service.refresh_portfolio(desired_yield)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
