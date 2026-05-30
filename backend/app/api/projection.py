"""Endpoints para projeção de renda passiva e análise setorial."""

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
    """
    Projeta evolução da renda passiva ao longo do tempo.

    Considera:
    - Carteira atual
    - Aportes mensais
    - Crescimento de dividendos
    - Valorização da carteira
    - Reinvestimento de dividendos
    """
    svc = ProjectionService()
    return await svc.project_passive_income(req)


@router.post("/projection/sector-allocation", response_model=SectorAllocationResponse)
async def analyze_sector_allocation(target_allocations: dict[str, float]):
    """
    Analisa alocação setorial da carteira vs. targets.

    Body exemplo:
    ```json
    {
        "Financeiro": 20,
        "Energia": 15,
        "Tecnologia": 25,
        "Saúde": 10,
        "Varejo": 10,
        "Outros": 20
    }
    ```
    """
    svc = ProjectionService()
    return await svc.analyze_sector_allocation(target_allocations)
