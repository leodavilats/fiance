from fastapi import APIRouter

from app.models import (
    PassiveIncomeProjectionRequest,
    PassiveIncomeProjectionResponse,
    SectorAllocationResponse,
)
from app.services import ProjectionService

router = APIRouter()


@router.post("/projection/passive-income", response_model=PassiveIncomeProjectionResponse)
async def project_passive_income(req: PassiveIncomeProjectionRequest):
    svc = ProjectionService()
    return await svc.project_passive_income(req)


@router.post("/projection/sector-allocation", response_model=SectorAllocationResponse)
async def analyze_sector_allocation(target_allocations: dict[str, float]):
    svc = ProjectionService()
    return await svc.analyze_sector_allocation(target_allocations)
