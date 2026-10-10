from __future__ import annotations

import sqlalchemy as sa
from alembic import context

from datajob.config import carregar, url_do_banco
from datajob.esquema import SCHEMA, metadata

target_metadata = metadata


def _url() -> str:
    configurada = context.config.get_main_option("sqlalchemy.url", None)
    return url_do_banco(configurada) if configurada else carregar().database_url


def run_migrations_online() -> None:
    engine = sa.create_engine(_url())
    with engine.connect() as connection:
        # A tabela de versão mora em `mercado`; o schema precisa existir antes dela.
        connection.execute(sa.text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=SCHEMA,
            include_schemas=True,
            include_name=lambda nome, tipo, _: tipo != "schema" or nome == SCHEMA,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise RuntimeError("O data-job não gera SQL offline: rode contra um banco.")
run_migrations_online()
