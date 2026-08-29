from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings
from app.core.context import get_request_session

logger = logging.getLogger("fiance.database")

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"


class Base(DeclarativeBase):
    pass


def _build_engine():
    settings = get_settings()
    url = settings.sqlalchemy_database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    if url.startswith("sqlite:///./"):
        Path(url.replace("sqlite:///./", "")).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _alembic_config():
    from alembic.config import Config

    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", str(engine.url))
    return config


def init_db() -> None:
    from alembic import command

    from app.models import db_models  # noqa: F401

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    config = _alembic_config()

    if not existing_tables:
        Base.metadata.create_all(bind=engine)
        command.stamp(config, "head")
        logger.info("Banco criado do zero e marcado na revisão mais recente.")
        return

    command.upgrade(config, "head")


_initialized = False


def ensure_initialized() -> None:
    global _initialized
    if not _initialized:
        init_db()
        _initialized = True


@contextmanager
def db_session():
    ensure_initialized()

    ambient = get_request_session()
    if ambient is not None:
        yield ambient
        ambient.flush()
        return

    session = SessionLocal()
    try:
        yield session
        session.commit()
    finally:
        session.close()
