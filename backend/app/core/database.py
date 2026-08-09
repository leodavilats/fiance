from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _build_engine():
    settings = get_settings()
    url = settings.sqlalchemy_database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    if url.startswith("sqlite:///./"):
        from pathlib import Path

        Path(url.replace("sqlite:///./", "")).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    from app.models import db_models  # noqa: F401 — registra os modelos no Base

    Base.metadata.create_all(bind=engine)
