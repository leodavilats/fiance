from fastapi import APIRouter

from app.models import Preferences, PreferencesRequest
from app.repositories import PortfolioRepository

router = APIRouter()

portfolio_repo = PortfolioRepository()


@router.get("/preferences", response_model=Preferences)
async def get_preferences() -> Preferences:
    return Preferences(**portfolio_repo.get_preferences())


@router.put("/preferences", response_model=Preferences)
async def save_preferences(req: PreferencesRequest) -> Preferences:
    portfolio_repo.set_preferences(req.cash_available)
    return Preferences(**portfolio_repo.get_preferences())
