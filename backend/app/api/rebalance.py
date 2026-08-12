from fastapi import APIRouter

from app.models import RebalanceResponse
from app.services import RebalanceService

router = APIRouter()


@router.get("/rebalance", response_model=RebalanceResponse)
async def rebalance() -> RebalanceResponse:
    svc = RebalanceService()
    return await svc.get_rebalance_plan()
