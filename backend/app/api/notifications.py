from fastapi import APIRouter
from pydantic import BaseModel

from app.repositories import PortfolioRepository

router = APIRouter()

portfolio_repo = PortfolioRepository()


class DeviceTokenRequest(BaseModel):
    token: str
    platform: str = "android"


@router.post("/notifications/register-token", status_code=204)
async def register_token(req: DeviceTokenRequest) -> None:
    portfolio_repo.register_device_token(req.token, req.platform)
