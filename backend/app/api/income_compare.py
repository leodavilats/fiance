from fastapi import APIRouter, Query

from app.models.income_compare import IncomeCompareResponse
from app.services.income_compare_service import IncomeCompareService

router = APIRouter()

service = IncomeCompareService()


@router.get("/income-compare", response_model=IncomeCompareResponse)
async def income_compare(
    amount: float = Query(10_000.0, gt=0, le=1e9, description="Valor a comparar (R$)"),
    horizon_months: int = Query(
        12, ge=1, le=600, description="Prazo considerado para a renda fixa"
    ),
) -> IncomeCompareResponse:
    """ "Com a Selic a 14,4%, vale mais o CDB ou o FII?" O comparador de renda fixa e o de ativos eram universos separados; o produto tinha os dois lados da conta e nunca os colocava na mesma tela."""
    return await service.compare(amount=amount, horizon_months=horizon_months)
