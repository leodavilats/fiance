from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.database import db_session
from app.models.db_models import User
from app.storage import event_store, portfolio_store

router = APIRouter()

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
    return _derive(user_id)


@router.post("/onboarding/complete", response_model=OnboardingState)
async def complete(
    body: CompleteRequest | None = None,
    user_id: str = Depends(get_current_user),
) -> OnboardingState:
    body = body or CompleteRequest()

    with db_session() as session:
        portfolio_store.ensure_user(session, user_id)

        user = session.get(User, user_id)
        if user is not None and user.onboarded_at is None:
            user.onboarded_at = time.time()

    if not event_store.has_event(user_id, "onboarding_completed"):
        event_store.record(
            user_id,
            "onboarding_completed",
            {"reason": "skipped" if body.skipped else "finished"},
            platform="server",
        )

    return _derive(user_id)
