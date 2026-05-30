"""Controller para goals de alocação."""

from fastapi import APIRouter

from app.models import Goal, GoalsRequest
from app.services import GoalService

router = APIRouter()

goal_service = GoalService()


@router.get("/goals", response_model=list[Goal])
async def get_goals() -> list[Goal]:
    """Retorna goals de alocação."""
    return goal_service.get_goals()


@router.put("/goals", response_model=list[Goal])
async def save_goals(req: GoalsRequest) -> list[Goal]:
    """Salva goals de alocação."""
    return goal_service.save_goals(req.goals)
