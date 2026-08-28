"""Onboarding em três passos, não bloqueante.

O critério de saída do produto é chegar ao primeiro diagnóstico em menos de três
minutos. Duas decisões vêm daí e valem estar escritas:

* **Nenhum passo bloqueia.** Pular leva a uma tela com conteúdo — a carteira de
  demonstração — e não a uma tela vazia com um convite. Onboarding que prende é
  onboarding que a pessoa fecha, e quem fecha não volta.
* **O estado é do servidor, não do navegador.** Guardar o progresso em
  `localStorage` faria o onboarding recomeçar em cada aparelho, e faria a
  métrica de ativação medir dispositivo em vez de pessoa.

`onboarded_at` mora em `users` porque é fato da conta. O passo corrente não
mora em lugar nenhum: ele é **derivado** do que a pessoa já fez. Guardar um
contador seria criar uma segunda verdade que diverge da primeira — alguém
importa a carteira por outro caminho e o onboarding continua pedindo isso.
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.database import db_session
from app.models.db_models import User
from app.storage import event_store, portfolio_store

router = APIRouter()

#: Mínimo para o veredito de risco ser emitido — o mesmo corte do funil.
READABLE_PORTFOLIO_SIZE = 4

STEP_PORTFOLIO = 2
STEP_GOALS = 3
TOTAL_STEPS = 3


class OnboardingState(BaseModel):
    step: int
    total_steps: int = TOTAL_STEPS
    completed: bool
    onboarded_at: float | None = None

    positions: int
    has_goals: bool

    #: Por que o passo é este. A tela mostra para que o usuário entenda o que
    #: falta, em vez de ver uma barra de progresso sem explicação.
    reason: str


class CompleteRequest(BaseModel):
    skipped: bool = False


def _derive(user_id: str) -> OnboardingState:
    positions = len(portfolio_store.list_positions(user_id))
    goals = portfolio_store.list_goals(user_id)

    with db_session() as session:
        user = session.get(User, user_id)
        onboarded_at = user.onboarded_at if user is not None else None

    if positions == 0:
        step, reason = STEP_PORTFOLIO, "Falta registrar a primeira posição."
    elif not goals:
        step, reason = STEP_GOALS, "Falta definir a primeira meta de alocação."
    else:
        step, reason = TOTAL_STEPS, "Tudo pronto."

    return OnboardingState(
        step=step,
        completed=onboarded_at is not None,
        onboarded_at=onboarded_at,
        positions=positions,
        has_goals=bool(goals),
        reason=reason,
    )


@router.get("/onboarding", response_model=OnboardingState)
async def read_state(user_id: str = Depends(get_current_user)) -> OnboardingState:
    """Onde a pessoa está, derivado do que ela já fez.

    Chamar isto num aparelho novo devolve o mesmo estado do primeiro — é o que
    faz o onboarding não recomeçar a cada login.
    """
    return _derive(user_id)


@router.post("/onboarding/complete", response_model=OnboardingState)
async def complete(
    body: CompleteRequest | None = None,
    user_id: str = Depends(get_current_user),
) -> OnboardingState:
    """Marca o onboarding como visto — inclusive quando foi pulado.

    Pular também conclui, de propósito: o objetivo do carimbo é não mostrar a
    sequência de novo, e insistir com quem já disse não é o caminho mais curto
    para a pessoa desinstalar.
    """
    body = body or CompleteRequest()

    with db_session() as session:
        # A conta pode não ter linha em `users` ainda: ela é criada de forma
        # preguiçosa na primeira escrita de carteira, e concluir o onboarding
        # sem ter cadastrado nada é justamente o caso de quem pulou.
        portfolio_store.ensure_user(session, user_id)

        user = session.get(User, user_id)
        if user is not None and user.onboarded_at is None:
            user.onboarded_at = time.time()

    # O evento é gravado pelo servidor porque é ele que decide a métrica de
    # ativação — depender do cliente faria a taxa variar por plataforma.
    if not event_store.has_event(user_id, "onboarding_completed"):
        event_store.record(
            user_id,
            "onboarding_completed",
            {"reason": "skipped" if body.skipped else "finished"},
            platform="server",
        )

    return _derive(user_id)
