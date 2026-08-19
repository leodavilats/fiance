from fastapi import APIRouter

from app.analysis.renda_fixa_analysis import (
    compare_options,
    get_reference_rates,
)
from app.models import (
    ReferenceRates,
    RendaFixaCompareRequest,
    RendaFixaCompareResponse,
)

router = APIRouter()


@router.get("/renda-fixa/taxas", response_model=ReferenceRates)
async def reference_rates() -> ReferenceRates:
    return get_reference_rates()


@router.post("/renda-fixa/comparar", response_model=RendaFixaCompareResponse)
async def compare_assets(req: RendaFixaCompareRequest) -> RendaFixaCompareResponse:
    return compare_options(req)
