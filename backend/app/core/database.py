from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings
from app.core.context import get_request_session, reset_request_session, set_request_session

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


class RevisaoDesconhecida(RuntimeError):
    pass


def _revisoes_conhecidas(config) -> set[str]:
    from alembic.script import ScriptDirectory

    return {revisao.revision for revisao in ScriptDirectory.from_config(config).walk_revisions()}


def _revisoes_do_banco() -> set[str]:
    from alembic.runtime.migration import MigrationContext

    with engine.connect() as connection:
        return set(MigrationContext.configure(connection).get_current_heads())


def _conferir_ponto_de_partida(config) -> None:
    carimbadas = _revisoes_do_banco()

    if not carimbadas:
        raise RevisaoDesconhecida(
            "O banco tem tabelas e não tem alembic_version: não dá para saber de onde migrar. "
            "Se não houver dado a preservar, recrie o schema — o boot num banco vazio o cria e "
            "carimba sozinho."
        )

    desconhecidas = carimbadas - _revisoes_conhecidas(config)
    if desconhecidas:
        raise RevisaoDesconhecida(
            f"O banco está carimbado em {', '.join(sorted(desconhecidas))}, que não existe mais "
            "nesta cadeia de migrações. O histórico foi colapsado depois que esse banco foi "
            "migrado pela última vez. Recriar o schema (se não houver dado) ou trazer o banco "
            "para a frente pela cadeia antiga, recuperável no git, antes de carimbar a atual."
        )


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

    _conferir_ponto_de_partida(config)
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


@contextmanager
def independent_session():
    ensure_initialized()

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def outside_request_transaction():
    token = set_request_session(None)
    try:
        yield
    finally:
        reset_request_session(token)
