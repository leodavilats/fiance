"""Os direitos correntes, para o cliente montar a UI a partir deles.

Os clientes **consultam**, nunca decidem: `features` e `limits` servem para
esconder botão que não faz nada e para desenhar a prévia certa, não para
liberar acesso. A checagem que vale é a do servidor, no `guard`.

Flag desligada some da UI: quando `unrestricted` é verdadeiro, o cliente não
deve mostrar gate nenhum — é o que permite o código de cobrança viver em
produção antes de a cobrança existir.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.entitlement import Feature, check, plans, resolve
from app.services import subscription_service

router = APIRouter()


@router.get("/entitlements")
async def read_entitlements(user_id: str = Depends(get_current_user)) -> dict:
    direitos = resolve(user_id)
    assinatura = subscription_service.get(user_id)

    return {
        **direitos.as_dict(),
        "subscription": {
            "status": assinatura["status"],
            "plan_code": assinatura["plan_code"],
            "interval": assinatura["interval"],
            "price_cents": assinatura["price_cents"],
            "locked": assinatura["locked"],
            "current_period_end": assinatura["current_period_end"],
        },
    }


@router.get("/entitlements/rules")
async def read_rules() -> dict:
    """A régua publicada, com a justificativa de cada linha.

    Está aqui para que a decisão possa ser discutida — e reaberta com
    argumento, não com apetite.
    """
    return {"rules": plans.as_dicts()}


@router.get("/entitlements/check/{feature}")
async def check_feature(feature: Feature, user_id: str = Depends(get_current_user)) -> dict:
    """Avalia **sem consumir**.

    A tela pergunta para decidir se desenha o gate, e perguntar não pode gastar
    a cota de quem só passou por ali.
    """
    return check(feature, user_id, cost=0).as_dict()
