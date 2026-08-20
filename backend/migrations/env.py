from __future__ import annotations

from alembic import context
from sqlalchemy import create_engine

from app.core.database import Base
from app.core.database import engine as app_engine
from app.models import db_models  # noqa: F401 — registra os modelos no Base

target_metadata = Base.metadata


def _engine():
    """Engine da migração.

    Usa a URL do config quando ela aponta para outro banco (testes de migração,
    `alembic upgrade` apontado para outro ambiente); cai no engine da aplicação
    no caso normal, que é o que já resolve DATABASE_URL.
    """
    configured = context.config.get_main_option("sqlalchemy.url", None)
    if configured and configured != str(app_engine.url):
        connect_args = {"check_same_thread": False} if configured.startswith("sqlite") else {}
        return create_engine(configured, connect_args=connect_args)
    return app_engine


def run_migrations_offline() -> None:
    engine = _engine()
    context.configure(
        url=str(engine.url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # SQLite não faz ALTER de coluna: batch mode reescreve a tabela.
        render_as_batch=engine.dialect.name == "sqlite",
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with _engine().connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=connection.dialect.name == "sqlite",
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
