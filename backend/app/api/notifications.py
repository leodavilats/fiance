from typing import Annotated, Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel, StringConstraints

from app.repositories import PortfolioRepository

router = APIRouter()

portfolio_repo = PortfolioRepository()

TOKEN_MIN = 32
TOKEN_MAX = 512
TOKEN_PATTERN = r"^[A-Za-z0-9_:\-]+$"

PushToken = Annotated[
    str,
    StringConstraints(min_length=TOKEN_MIN, max_length=TOKEN_MAX, pattern=TOKEN_PATTERN),
]


class DeviceTokenRequest(BaseModel):
    token: PushToken
    platform: Literal["android", "ios"] = "android"


@router.post("/notifications/register-token", status_code=204)
async def register_token(req: DeviceTokenRequest) -> None:
    portfolio_repo.register_device_token(req.token, req.platform)


@router.delete("/notifications/register-token", status_code=204)
async def unregister_token(
    token: str = Query(..., min_length=TOKEN_MIN, max_length=TOKEN_MAX, pattern=TOKEN_PATTERN),
) -> None:
    portfolio_repo.unregister_device_token(token)
