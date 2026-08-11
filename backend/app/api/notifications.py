from fastapi import APIRouter
from pydantic import BaseModel

from app.notifications import send_push
from app.repositories import PortfolioRepository

router = APIRouter()

portfolio_repo = PortfolioRepository()


class DeviceTokenRequest(BaseModel):
    token: str
    platform: str = "android"


class TestNotificationResponse(BaseModel):
    tokens_found: int
    invalid_tokens: int


@router.post("/notifications/register-token", status_code=204)
async def register_token(req: DeviceTokenRequest) -> None:
    portfolio_repo.register_device_token(req.token, req.platform)


@router.delete("/notifications/register-token", status_code=204)
async def unregister_token(token: str) -> None:
    portfolio_repo.unregister_device_token(token)


@router.post("/notifications/test", response_model=TestNotificationResponse)
async def send_test_notification() -> TestNotificationResponse:
    tokens = [t["token"] for t in portfolio_repo.list_device_tokens()]
    invalid = send_push(
        tokens,
        title="fianceAI",
        body="Notificação de teste — se você está vendo isso, está tudo funcionando!",
        data={"type": "test"},
    )
    for token in invalid:
        portfolio_repo.unregister_device_token(token)
    return TestNotificationResponse(tokens_found=len(tokens), invalid_tokens=len(invalid))
