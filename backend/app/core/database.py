from __future__ import annotations

import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

logger = logging.getLogger("fianceai.database")


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
    _add_missing_columns()


def _add_missing_columns() -> None:
    # Sem Alembic: create_all() nunca adiciona colunas a tabelas já existentes,
    # então bancos criados antes de um novo campo no model ficam desatualizados.
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue

            existing_columns = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_columns:
                    continue

                col_type = column.type.compile(dialect=engine.dialect)
                default_sql = ""
                default = column.default
                if default is not None and getattr(default, "is_scalar", False):
                    value = default.arg
                    if isinstance(value, bool):
                        # Postgres exige TRUE/FALSE (não 1/0) para coluna BOOLEAN.
                        default_sql = f" DEFAULT {'TRUE' if value else 'FALSE'}"
                    elif isinstance(value, int | float):
                        default_sql = f" DEFAULT {value}"
                    elif isinstance(value, str):
                        default_sql = f" DEFAULT '{value}'"

                # NOT NULL só é seguro com DEFAULT pra preencher linhas existentes.
                not_null_sql = " NOT NULL" if (not column.nullable and default_sql) else ""

                ddl = (
                    f'ALTER TABLE "{table.name}" '
                    f'ADD COLUMN "{column.name}" {col_type}{default_sql}{not_null_sql}'
                )
                conn.execute(text(ddl))
                logger.info("Migração leve: %s.%s adicionada", table.name, column.name)
