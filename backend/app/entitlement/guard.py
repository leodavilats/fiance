"""A dependência FastAPI que aplica a régua.

Bloqueio é **402 com corpo explicativo**: qual feature foi pedida, qual plano
ela exige, quanto do teto já foi usado. A UI monta o gate a partir da resposta,
então o texto do paywall não duplica a régua — e mudar a régua não exige mexer
no cliente.

402 e não 403: 403 diz "você não pode", 402 diz "isto custa". A diferença
importa para o cliente saber que existe um caminho, e para a telemetria separar
falta de permissão de falta de plano.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request

from app.core.auth import get_current_user
from app.storage import event_store

from .plans import Feature
from .resolve import Decision, check


class PaymentRequired(HTTPException):
    """402 com o corpo que a UI precisa para montar o gate."""

    def __init__(self, decision: Decision):
        super().__init__(status_code=402, detail=decision.as_dict())


def _record_limit_event(user_id: str, decision: Decision, origin: str) -> None:
    """Encostar no limite é o sinal que decide onde o paywall deve estar.

    Sem isto, a única informação sobre a cerca seria quantas pessoas pagaram —
    e não quantas bateram nela e desistiram, que é o número que diz se ela está
    no lugar certo.
    """
    try:
        event_store.record(
            user_id,
            "limit_reached" if decision.limit_reached else "paywall_viewed",
            {"feature": decision.feature.value, "plan": decision.plan.value, "origin": origin},
            platform="server",
        )
    except Exception:
        # Instrumentação nunca derruba a resposta.
        pass


def requires(feature: Feature, cost: int = 1) -> Callable:
    """Dependência que exige a feature e consome o teto quando permitido.

    `cost=0` só verifica — use em leitura que não deve gastar cota.
    """

    async def _guard(request: Request, user_id: str = Depends(get_current_user)) -> Decision:
        decision = check(feature, user_id, cost=cost)
        if not decision.allowed:
            _record_limit_event(user_id, decision, origin=request.url.path)
            raise PaymentRequired(decision)
        return decision

    return _guard


def peek(feature: Feature) -> Callable:
    """Avalia sem consumir e **sem bloquear**.

    Para telas que mostram prévia: elas precisam saber que o gate existe para
    desenhar a prévia, e perguntar não pode gastar a cota de quem só passou.
    """

    async def _peek(user_id: str = Depends(get_current_user)) -> Decision:
        return check(feature, user_id, cost=0)

    return _peek
