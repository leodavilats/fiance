from datetime import date

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.core.pagination import MAX_PAGE_SIZE
from app.models.dividends import (
    DividendReceived,
    DividendReceivedCreate,
    DividendReceivedUpdate,
    DividendsReceivedResponse,
)
from app.services.dividend_calendar_service import DividendCalendarService
from app.services.dividends_service import DividendsService

router = APIRouter()

service = DividendsService()
calendar_service = DividendCalendarService()


@router.get("/dividends/received", response_model=DividendsReceivedResponse)
async def list_received(
    estimated_monthly: float | None = Query(
        None,
        ge=0,
        description="Estimativa mensal do dashboard, para comparar com o recebido de fato",
    ),
    limit: int | None = Query(None, ge=1, le=MAX_PAGE_SIZE),
    cursor: str | None = Query(None, description="Cursor devolvido em `next_cursor`."),
) -> DividendsReceivedResponse:
    """Proventos efetivamente creditados, com totais por mês e por ativo."""
    return service.list_received(estimated_monthly=estimated_monthly, limit=limit, cursor=cursor)


@router.post("/dividends/received", response_model=DividendReceived, status_code=201)
async def create_received(req: DividendReceivedCreate) -> DividendReceived:
    return service.create(req)


@router.put("/dividends/received/{dividend_id}", response_model=DividendReceived)
async def update_received(dividend_id: int, req: DividendReceivedUpdate) -> DividendReceived:
    return service.update(dividend_id, req)


@router.delete("/dividends/received/{dividend_id}")
async def delete_received(dividend_id: int) -> dict:
    return service.delete(dividend_id)


class DividendConfirmItem(BaseModel):
    ticker: str
    paid_at: date
    amount: float = Field(gt=0, le=1e9)
    kind: str = "dividendo"


class DividendConfirmRequest(BaseModel):
    items: list[DividendConfirmItem] = Field(default_factory=list)


@router.get("/dividends/pending")
async def pending_dividends() -> dict:
    """Proventos que o calendário sugere, cruzados com a sua carteira.

    Leitura pura: nada é gravado aqui. A confirmação é um passo separado de
    propósito — cada fonte de erro possível nesta lista (data-com, razão
    incompleto, JCP bruto) erra o valor **para mais**, e provento inventado
    infla renda passiva e vira número errado na declaração.
    """
    return await calendar_service.pending()


@router.post("/dividends/pending/confirm")
async def confirm_dividends(body: DividendConfirmRequest) -> dict:
    """Grava os proventos que o usuário confirmou, e só esses."""
    if not body.items:
        return {"created": 0, "items": []}

    criados = [
        service.create(
            DividendReceivedCreate(
                ticker=item.ticker,
                paid_at=item.paid_at,
                amount=item.amount,
                kind=item.kind,
                note="Confirmado a partir do calendário de proventos.",
            )
        )
        for item in body.items
    ]

    return {"created": len(criados), "items": [c.model_dump() for c in criados]}
