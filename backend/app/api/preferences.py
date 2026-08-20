from fastapi import APIRouter

from app.models import Preferences, PreferencesRequest
from app.repositories import PortfolioRepository

router = APIRouter()

portfolio_repo = PortfolioRepository()


def _with_push_status(prefs: dict) -> Preferences:
    devices = portfolio_repo.list_device_tokens()
    return Preferences(
        **prefs,
        registered_devices=len(devices),
        push_enabled=bool(devices),
    )


@router.get("/preferences", response_model=Preferences)
async def get_preferences() -> Preferences:
    return _with_push_status(portfolio_repo.get_preferences())


@router.put("/preferences", response_model=Preferences)
async def save_preferences(req: PreferencesRequest) -> Preferences:
    # exclude_unset: um PUT parcial não zera o que não veio no corpo. Enviar
    # `null` explicitamente continua limpando o campo (ex.: passive_income_goal).
    fields = req.model_dump(exclude_unset=True, mode="json")
    portfolio_repo.set_preferences(**fields)
    return _with_push_status(portfolio_repo.get_preferences())
