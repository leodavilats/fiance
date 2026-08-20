from fastapi import APIRouter

from app.models.renda_fixa import (
    FixedIncomeCreateRequest,
    FixedIncomeListResponse,
    FixedIncomePosition,
    FixedIncomeUpdateRequest,
)
from app.services.fixed_income_service import FixedIncomeService

router = APIRouter()

service = FixedIncomeService()


@router.get("/fixed-income", response_model=FixedIncomeListResponse)
async def list_fixed_income() -> FixedIncomeListResponse:
    """Posições de renda fixa marcadas a mercado pelo backend."""
    return service.list_positions()


@router.post("/fixed-income", response_model=FixedIncomePosition, status_code=201)
async def create_fixed_income(req: FixedIncomeCreateRequest) -> FixedIncomePosition:
    return service.create(req)


@router.put("/fixed-income/{position_id}", response_model=FixedIncomePosition)
async def update_fixed_income(
    position_id: int, req: FixedIncomeUpdateRequest
) -> FixedIncomePosition:
    return service.update(position_id, req)


@router.delete("/fixed-income/{position_id}")
async def delete_fixed_income(position_id: int) -> dict:
    return service.delete(position_id)
