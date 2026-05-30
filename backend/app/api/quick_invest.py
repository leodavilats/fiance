"""Endpoint para Quick Invest - recomendação rápida de investimentos."""

from fastapi import APIRouter

from app.models import QuickInvestRequest, QuickInvestResponse
from app.services import QuickInvestService

router = APIRouter()


@router.post("/quick-invest", response_model=QuickInvestResponse)
async def quick_invest(req: QuickInvestRequest):
    """
    Recomendação rápida de investimentos.

    Analisa a carteira atual, compara com metas de alocação e sugere
    investimentos inteligentes priorizando:
    - Rebalanceamento de categorias
    - Melhores oportunidades por score
    - Diversificação

    Ideal para quando você recebe o salário e quer investir rapidamente.
    """
    svc = QuickInvestService()
    return await svc.quick_invest(req)
