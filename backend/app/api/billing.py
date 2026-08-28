"""Rotas de cobrança.

O webhook fica **fora** do router protegido: quem chama é o gateway, não um
usuário com sessão. O que o autentica é a assinatura HMAC do corpo — e é por
isso que ela é verificada antes de qualquer outra coisa: webhook sem
verificação é uma rota pública que concede assinatura.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from app.core.auth import get_current_user, require_admin
from app.core.errors import DomainError
from app.payments import SignatureError, UnknownPlanError, billing

router = APIRouter()

public_router = APIRouter()

admin_router = APIRouter()


class CheckoutRequest(BaseModel):
    plan_code: str


class UnknownPlan(DomainError):
    status_code = 422


@router.get("/billing/plans")
async def read_plans() -> dict:
    """O catálogo vigente. Quem já assinou carrega o próprio preço."""
    return {"offers": billing.offers()}


@router.post("/billing/checkout")
async def create_checkout(body: CheckoutRequest, user_id: str = Depends(get_current_user)) -> dict:
    """Cria a sessão de pagamento. Não concede nada — quem concede é o webhook."""
    try:
        return billing.start_checkout(user_id, body.plan_code)
    except UnknownPlanError as exc:
        raise UnknownPlan(str(exc)) from exc


@public_router.post("/billing/webhook")
async def receive_webhook(
    request: Request,
    signature: str = Header(default="", alias="X-Signature"),
) -> dict:
    """Recebe evento do gateway.

    Responde 200 mesmo para evento repetido: o provedor reenvia até receber
    200, e devolver erro num reenvio legítimo o faria tentar para sempre.
    """
    corpo = await request.body()

    try:
        billing.provider().verify(corpo, signature)
    except SignatureError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    import json

    try:
        payload = json.loads(corpo or b"{}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Corpo não é JSON válido.") from exc

    evento = billing.provider().parse(payload)
    if not evento.id:
        raise HTTPException(status_code=400, detail="Evento sem identificador.")

    try:
        return billing.handle_event(evento)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@admin_router.get("/billing/reconciliation")
async def read_reconciliation(_: str = Depends(require_admin)) -> dict:
    """O que o gateway diz estar ativo contra o que foi concedido."""
    return billing.reconcile()
