from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel

from app.core import sessions
from app.core.auth import get_current_user
from app.core.brt import now_brt
from app.core.errors import DomainError
from app.storage import account_store

router = APIRouter()


class ConfirmDeletion(BaseModel):
    confirm: str = ""


class DeletionNotConfirmed(DomainError):
    status_code = 400


@router.get("/account/export")
async def export_account(user_id: str = Depends(get_current_user)) -> Response:
    """Baixa tudo que é do usuário. Sem gate: nos dois planos, sempre."""
    payload = account_store.export_account(user_id)
    stamp = now_brt().strftime("%Y-%m-%d")
    body = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    return Response(
        content=body,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="fiance-{stamp}.json"'},
    )


@router.get("/account/deletion-policy")
async def deletion_policy() -> dict:
    """O que a exclusão remove e em quanto tempo — dito antes de perguntar."""
    return {
        "sla_days": account_store.DELETION_SLA_DAYS,
        "removes": sorted(label for label, _ in account_store.USER_SCOPED_MODELS),
        "note": (
            "A remoção é imediata no banco de produção. O prazo declarado cobre "
            "backups e réplicas, onde o dado ainda pode existir até serem "
            "rotacionados. Nada disso está atrás de plano."
        ),
        "confirmation_phrase": "EXCLUIR",
    }


@router.delete("/account")
async def delete_account(
    body: ConfirmDeletion | None = None,
    user_id: str = Depends(get_current_user),
) -> dict:
    """Exclui a conta. Exige confirmação escrita e encerra toda sessão viva."""
    body = body or ConfirmDeletion()
    if body.confirm.strip().upper() != "EXCLUIR":
        raise DeletionNotConfirmed(
            'Envie {"confirm": "EXCLUIR"} para confirmar a exclusão definitiva da conta.'
        )

    # `delete_account` já carimba o corte de sessão na lápide; a chamada
    # explícita cobre o caso de a linha de `users` não existir (conta criada
    # implicitamente por escrita, sem login pelo Google).
    sessions.revoke_all_for_user(user_id)
    removed = account_store.delete_account(user_id)

    return {
        "deleted": True,
        "removed": removed,
        "sla_days": account_store.DELETION_SLA_DAYS,
    }
