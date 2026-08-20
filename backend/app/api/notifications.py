from fastapi import APIRouter, Query
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


@router.delete("/notifications/register-token", status_code=204)
async def unregister_token(token: str = Query(..., min_length=8, max_length=512)) -> None:
    """Desassocia o token deste aparelho do usuário atual.

    O DELETE havia sido removido do backend: depois do logout o aparelho
    continuava recebendo o resumo de carteira da conta anterior até que alguém
    registrasse o token de novo.
    """
    portfolio_repo.unregister_device_token(token)
