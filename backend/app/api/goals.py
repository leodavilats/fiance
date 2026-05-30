"""Controller para goals de alocação."""

from fastapi import APIRouter

from app.models import Goal, GoalsRequest, SectorGoal, SectorGoalsRequest
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


@router.get("/sector-goals", response_model=list[SectorGoal])
async def get_sector_goals() -> list[SectorGoal]:
    """Retorna sector goals de alocação."""
    return goal_service.get_sector_goals()


@router.put("/sector-goals", response_model=list[SectorGoal])
async def save_sector_goals(req: SectorGoalsRequest) -> list[SectorGoal]:
    """Salva sector goals de alocação."""
    return goal_service.save_sector_goals(req.sector_goals)
