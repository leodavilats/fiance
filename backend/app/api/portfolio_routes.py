from fastapi import APIRouter

from app.models import (
    ClosedTrade,
    ClosedTradesResponse,
    PortfolioEvaluationRequest,
    PortfolioEvaluationResponse,
    PortfolioItem,
    PortfolioStateResponse,
    SavePortfolioRequest,
    SellRequest,
)
from app.services import PortfolioService

router = APIRouter()

portfolio_service = PortfolioService()


@router.post("/portfolio/evaluate", response_model=PortfolioEvaluationResponse)
async def evaluate_portfolio(req: PortfolioEvaluationRequest) -> PortfolioEvaluationResponse:
    return await portfolio_service.evaluate_portfolio(req)


@router.get("/portfolio", response_model=PortfolioStateResponse)
async def get_portfolio() -> PortfolioStateResponse:
    return portfolio_service.get_portfolio()


@router.put("/portfolio", response_model=PortfolioStateResponse)
async def save_portfolio(req: SavePortfolioRequest) -> PortfolioStateResponse:
    """Importação explícita: substitui a carteira inteira (destrutivo)."""
    return portfolio_service.save_portfolio(req)


@router.post("/portfolio/position", response_model=PortfolioStateResponse)
async def upsert_position(item: PortfolioItem) -> PortfolioStateResponse:
    """Cria/atualiza uma posição sem tocar nas outras."""
    return portfolio_service.upsert_position(item)


@router.delete("/portfolio/position/{ticker}", response_model=PortfolioStateResponse)
async def delete_position_by_item(ticker: str) -> PortfolioStateResponse:
    portfolio_service.delete_position(ticker)
    return portfolio_service.get_portfolio()


@router.delete("/portfolio/{ticker}")
async def delete_position(ticker: str) -> dict:
    """Compatibilidade: prefira DELETE /portfolio/position/{ticker}."""
    return portfolio_service.delete_position(ticker)


@router.post("/portfolio/sell", response_model=ClosedTrade)
async def sell_position(req: SellRequest) -> ClosedTrade:
    return await portfolio_service.sell_position(req)


@router.get("/portfolio/trades", response_model=ClosedTradesResponse)
async def get_closed_trades() -> ClosedTradesResponse:
    return portfolio_service.get_closed_trades()
