from __future__ import annotations

import time

from sqlalchemy import func, select

from app.core.database import db_session
from app.models.db_models import InterestSignupDb


def register(email: str, source: str = "landing") -> bool:
    normalizado = email.strip().lower()

    with db_session() as session:
        existente = session.scalars(
            select(InterestSignupDb).where(InterestSignupDb.email == normalizado)
        ).first()
        if existente is not None:
            return False

        session.add(InterestSignupDb(email=normalizado, source=source, created_at=time.time()))
        return True


def count() -> int:
    with db_session() as session:
        return int(session.scalar(select(func.count()).select_from(InterestSignupDb)) or 0)
