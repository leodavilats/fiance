"""Controller para goals de alocação."""

from typing import List

from fastapi import APIRouter

from app.models import Goal, GoalsRequest
from app.repositories import PortfolioRepository

router = APIRouter()

portfolio_repo = PortfolioRepository()


@router.get("/goals", response_model=List[Goal])
async def get_goals() -> List[Goal]:
    """Retorna goals de alocação."""
    goals = portfolio_repo.list_goals()
    if not goals:
        return [
            Goal(category="renda", target_pct=40),
            Goal(category="trade", target_pct=50),
            Goal(category="cripto", target_pct=5),
            Goal(category="caixa", target_pct=5),
        ]
    return [Goal(**g) for g in goals]


@router.put("/goals", response_model=List[Goal])
async def save_goals(req: GoalsRequest) -> List[Goal]:
    """Salva goals de alocação."""
    portfolio_repo.replace_goals(
        [{"category": g.category, "target_pct": g.target_pct} for g in req.goals]
    )
    return [Goal(**g) for g in portfolio_repo.list_goals()]
