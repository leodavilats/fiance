from fastapi import APIRouter

from app.models import QuickInvestRequest, QuickInvestResponse
from app.services import QuickInvestService

router = APIRouter()


@router.post("/quick-invest", response_model=QuickInvestResponse)
async def quick_invest(req: QuickInvestRequest):
    svc = QuickInvestService()
    return await svc.quick_invest(req)
