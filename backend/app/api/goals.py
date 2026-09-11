from fastapi import APIRouter

from app.models import Goal, GoalsRequest, SectorGoalResponse, SectorGoalsRequest
from app.services import GoalService

router = APIRouter()

goal_service = GoalService()


@router.get("/goals", response_model=list[Goal])
async def get_goals() -> list[Goal]:
    return goal_service.get_goals()


@router.put("/goals", response_model=list[Goal])
async def save_goals(req: GoalsRequest) -> list[Goal]:
    return goal_service.save_goals(req.goals)


@router.get("/sector-goals", response_model=list[SectorGoalResponse])
async def get_sector_goals() -> list[SectorGoalResponse]:
    declaradas = goal_service.has_declared_sector_goals()
    return [
        SectorGoalResponse(**g.model_dump(), declared=declaradas)
        for g in goal_service.get_sector_goals()
    ]


@router.put("/sector-goals", response_model=list[SectorGoalResponse])
async def save_sector_goals(req: SectorGoalsRequest) -> list[SectorGoalResponse]:
    salvas = goal_service.save_sector_goals(req.sector_goals)
    return [SectorGoalResponse(**g.model_dump(), declared=True) for g in salvas]
