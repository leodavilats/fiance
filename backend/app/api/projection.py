from fastapi import APIRouter, Depends

from app.entitlement import Feature, requires
from app.models import (
    PassiveIncomeProjectionRequest,
    PassiveIncomeProjectionResponse,
)
from app.services import ProjectionService

router = APIRouter()


@router.post(
    "/projection/passive-income",
    response_model=PassiveIncomeProjectionResponse,
    dependencies=[Depends(requires(Feature.PROJECTION))],
)
async def project_passive_income(req: PassiveIncomeProjectionRequest):
    svc = ProjectionService()
    return await svc.project_passive_income(req)
