from fastapi import APIRouter

from app.models import (
    PassiveIncomeProjectionRequest,
    PassiveIncomeProjectionResponse,
)
from app.services import ProjectionService

router = APIRouter()


@router.post("/projection/passive-income", response_model=PassiveIncomeProjectionResponse)
async def project_passive_income(req: PassiveIncomeProjectionRequest):
    svc = ProjectionService()
    return await svc.project_passive_income(req)
