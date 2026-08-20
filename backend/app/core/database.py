from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

logger = logging.getLogger("fiance.database")

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"

# Revisão que representa o schema no momento em que o Alembic foi introduzido.
# Bancos criados antes disso são marcados aqui e seguem em frente pelas
# migrações, em vez de serem recriados.
BASELINE_REVISION = "0001_baseline"


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
    """Deixa o banco no schema mais recente.

    Três caminhos, para que a introdução do Alembic não exija passo manual:

    - **banco novo**: `create_all` cria tudo e marcamos como já migrado
      (`stamp head`) — mais rápido que rodar a cadeia toda, e é o caminho dos
      testes;
    - **banco pré-Alembic** (tem tabelas, não tem `alembic_version`): marcamos
      na revisão baseline e aplicamos as migrações a partir dela;
    - **banco já versionado**: `upgrade head`.
    """
    from alembic import command

    from app.models import db_models  # noqa: F401 — registra os modelos no Base

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    config = _alembic_config()

    if not existing_tables:
        Base.metadata.create_all(bind=engine)
        command.stamp(config, "head")
        logger.info("Banco criado do zero e marcado na revisão mais recente.")
        return

    if "alembic_version" not in existing_tables:
        command.stamp(config, BASELINE_REVISION)
        logger.info(
            "Banco pré-Alembic detectado: marcado em %s antes de migrar.", BASELINE_REVISION
        )

    command.upgrade(config, "head")
