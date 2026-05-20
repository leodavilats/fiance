"""Controller para watchlist."""

from typing import List

from fastapi import APIRouter

from app.models import WatchlistItem, WatchlistRequest
from app.repositories import PortfolioRepository

router = APIRouter()

portfolio_repo = PortfolioRepository()


@router.get("/watchlist", response_model=List[WatchlistItem])
async def get_watchlist() -> List[WatchlistItem]:
    """Retorna a watchlist."""
    return [WatchlistItem(**w) for w in portfolio_repo.list_watchlist()]


@router.put("/watchlist", response_model=List[WatchlistItem])
async def save_watchlist(req: WatchlistRequest) -> List[WatchlistItem]:
    """Salva a watchlist."""
    portfolio_repo.replace_watchlist([{"ticker": i.ticker, "note": i.note} for i in req.items])
    return [WatchlistItem(**w) for w in portfolio_repo.list_watchlist()]


@router.delete("/watchlist/{ticker}")
async def delete_watchlist(ticker: str) -> dict:
    """Remove item da watchlist."""
    portfolio_repo.remove_watchlist(ticker)
    return {"deleted": ticker.upper()}
