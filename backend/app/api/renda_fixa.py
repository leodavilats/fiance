from fastapi import APIRouter

from app.analysis.renda_fixa_analysis import (
    analyze_one,
    compare_options,
    get_reference_rates,
)
from app.models import (
    ReferenceRates,
    RendaFixaAnalysisResult,
    RendaFixaAsset,
    RendaFixaCompareRequest,
    RendaFixaCompareResponse,
)

router = APIRouter()


@router.get("/renda-fixa/taxas", response_model=ReferenceRates)
async def reference_rates() -> ReferenceRates:
    return get_reference_rates()


@router.post("/renda-fixa/analisar", response_model=RendaFixaAnalysisResult)
async def analyze_asset(ativo: RendaFixaAsset) -> RendaFixaAnalysisResult:
    return analyze_one(ativo)


@router.post("/renda-fixa/comparar", response_model=RendaFixaCompareResponse)
async def compare_assets(req: RendaFixaCompareRequest) -> RendaFixaCompareResponse:
    return compare_options(req)
