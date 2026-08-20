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
    # exclude_unset: um PUT parcial não zera o que não veio no corpo. Enviar
    # `null` explicitamente continua limpando o campo (ex.: passive_income_goal).
    fields = req.model_dump(exclude_unset=True, mode="json")
    portfolio_repo.set_preferences(**fields)
    return Preferences(**portfolio_repo.get_preferences())
