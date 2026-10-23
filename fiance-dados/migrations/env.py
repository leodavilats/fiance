from __future__ import annotations

import os

import sqlalchemy as sa
from alembic import context

from dadosapi.config import url_do_banco

SCHEMA = "acesso"


def _url() -> str:
    configurada = context.config.get_main_option("sqlalchemy.url", None)
    return url_do_banco(configurada or os.environ["DATABASE_URL"])


def run_migrations_online() -> None:
    engine = sa.create_engine(_url())
    with engine.connect() as connection:
        # A tabela de versão mora em `acesso`, longe da do data-job em `mercado`. O IF NOT EXISTS
        # pede CREATE no banco até quando o schema existe; o papel dados_api não tem.
        existe = connection.execute(
            sa.text("SELECT 1 FROM pg_namespace WHERE nspname = :s"), {"s": SCHEMA}
        ).first()
        if existe is None:
            connection.execute(sa.text(f"CREATE SCHEMA {SCHEMA}"))
        connection.commit()
        context.configure(
            connection=connection,
            version_table_schema=SCHEMA,
            include_schemas=True,
            include_name=lambda nome, tipo, _: tipo != "schema" or nome == SCHEMA,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise RuntimeError("A fiance-dados não gera SQL offline: rode contra um banco.")
run_migrations_online()
