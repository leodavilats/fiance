from fastapi import APIRouter, Depends

from app import affirmation
from app.entitlement import Feature, requires
from app.models import QuickInvestRequest
from app.services import QuickInvestService

router = APIRouter()


@router.post(
    "/quick-invest",
    dependencies=[Depends(requires(Feature.QUICK_INVEST))],
)
async def quick_invest(req: QuickInvestRequest) -> dict:
    svc = QuickInvestService()
    resultado = await svc.quick_invest(req)
    return affirmation.apply(resultado.model_dump())
