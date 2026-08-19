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
    portfolio_repo.set_preferences(
        passive_income_goal=req.passive_income_goal,
        desired_yield_stock=req.desired_yield_stock,
        desired_yield_fii=req.desired_yield_fii,
        desired_yield_bdr=req.desired_yield_bdr,
        desired_yield_etf=req.desired_yield_etf,
        notify_price_alerts=req.notify_price_alerts,
        notify_new_opportunities=req.notify_new_opportunities,
    )
    return Preferences(**portfolio_repo.get_preferences())
