from fastapi import APIRouter, Query

from app.models.dividends import (
    DividendReceived,
    DividendReceivedCreate,
    DividendReceivedUpdate,
    DividendsReceivedResponse,
)
from app.services.dividends_service import DividendsService

router = APIRouter()

service = DividendsService()


@router.get("/dividends/received", response_model=DividendsReceivedResponse)
async def list_received(
    estimated_monthly: float | None = Query(
        None,
        ge=0,
        description="Estimativa mensal do dashboard, para comparar com o recebido de fato",
    ),
) -> DividendsReceivedResponse:
    """Proventos efetivamente creditados, com totais por mês e por ativo."""
    return service.list_received(estimated_monthly=estimated_monthly)


@router.post("/dividends/received", response_model=DividendReceived, status_code=201)
async def create_received(req: DividendReceivedCreate) -> DividendReceived:
    return service.create(req)


@router.put("/dividends/received/{dividend_id}", response_model=DividendReceived)
async def update_received(dividend_id: int, req: DividendReceivedUpdate) -> DividendReceived:
    return service.update(dividend_id, req)


@router.delete("/dividends/received/{dividend_id}")
async def delete_received(dividend_id: int) -> dict:
    return service.delete(dividend_id)
