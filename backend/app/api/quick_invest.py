from fastapi import APIRouter, Depends

from app.entitlement import Feature, requires
from app.models import QuickInvestRequest, QuickInvestResponse
from app.services import QuickInvestService

router = APIRouter()


@router.post(
    "/quick-invest",
    response_model=QuickInvestResponse,
    dependencies=[Depends(requires(Feature.QUICK_INVEST))],
)
async def quick_invest(req: QuickInvestRequest):
    svc = QuickInvestService()
    return await svc.quick_invest(req)
