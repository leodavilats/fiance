from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.services import referral_service

router = APIRouter()


class ReferralStatus(BaseModel):
    code: str = Field(..., description="O código que a pessoa compartilha")
    reward_days: int = Field(..., description="Dias de Premium por indicação qualificada")
    max_credited_days: int = Field(..., description="Teto de crédito acumulado, em dias")
    attributed: int = Field(..., description="Contas que chegaram pelo código")
    qualified: int = Field(..., description="Quantas dessas salvaram a primeira posição")
    pending: int = Field(..., description="Chegaram mas ainda não montaram carteira")
    days_earned: int = Field(..., description="Dias já creditados por indicação")
    credited_until: float | None = Field(None, description="Fim do Premium concedido")
    credited_days_total: int = Field(..., description="Total creditado, para o teto")


class RotateResponse(BaseModel):
    code: str


@router.get("/referral", response_model=ReferralStatus)
async def get_referral(user_id: str = Depends(get_current_user)) -> ReferralStatus:
    return ReferralStatus(**referral_service.status(user_id))


@router.post("/referral/rotate", response_model=RotateResponse)
async def rotate_referral(user_id: str = Depends(get_current_user)) -> RotateResponse:
    try:
        return RotateResponse(code=referral_service.rotate_code(user_id))
    except referral_service.ReferralError as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro
