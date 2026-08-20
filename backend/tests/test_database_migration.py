"""Migrações versionadas (Alembic).

Substitui os testes do migrador caseiro `_add_missing_columns`, que só sabia
adicionar coluna: não renomeava, não mudava tipo, não fazia backfill de dado
derivado e interpolava defaults em SQL por string.
"""

import os
import tempfile

import pytest
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

from app.core.database import BASELINE_REVISION, _alembic_config, engine, init_db


def _config_for(url: str):
    config = _alembic_config()
    config.set_main_option("sqlalchemy.url", url)
    return config


@pytest.fixture()
def sqlite_url():
    path = os.path.join(tempfile.mkdtemp(prefix="fiance_alembic_"), "mig.db")
    yield f"sqlite:///{path}"


def test_upgrade_head_from_empty_database_creates_every_table(sqlite_url):
    command.upgrade(_config_for(sqlite_url), "head")

    tables = set(inspect(create_engine(sqlite_url)).get_table_names())
    for expected in (
        "users",
        "portfolio",
        "portfolio_snapshot",
        "preferences",
        "goals",
        "closed_trades",
        "fixed_income_positions",
        "alembic_version",
    ):
        assert expected in tables


def test_downgrade_then_upgrade_round_trips(sqlite_url):
    config = _config_for(sqlite_url)
    command.upgrade(config, "head")
    command.downgrade(config, "base")

    remaining = set(inspect(create_engine(sqlite_url)).get_table_names())
    assert "portfolio" not in remaining

    command.upgrade(config, "head")
    assert "portfolio" in set(inspect(create_engine(sqlite_url)).get_table_names())


def test_pre_alembic_database_is_stamped_and_migrated(sqlite_url):
    """Banco criado antes do Alembic não pode ser recriado nem quebrar.

    Simula o estado real: tabelas do baseline presentes, sem
    `alembic_version` e sem a tabela nova de renda fixa.
    """
    config = _config_for(sqlite_url)
    command.upgrade(config, BASELINE_REVISION)

    legacy_engine = create_engine(sqlite_url)
    with legacy_engine.begin() as conn:
        conn.execute(text("DROP TABLE alembic_version"))

    assert "alembic_version" not in set(inspect(legacy_engine).get_table_names())
    assert "fixed_income_positions" not in set(inspect(legacy_engine).get_table_names())

    command.stamp(config, BASELINE_REVISION)
    command.upgrade(config, "head")

    tables = set(inspect(create_engine(sqlite_url)).get_table_names())
    assert "fixed_income_positions" in tables
    assert "portfolio" in tables


def test_legacy_rf_positions_are_removed_by_the_fixed_income_migration(sqlite_url):
    """As posições RF_* só tinham o valor investido; o resto vivia no navegador."""
    config = _config_for(sqlite_url)
    command.upgrade(config, BASELINE_REVISION)

    legacy_engine = create_engine(sqlite_url)
    with legacy_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (id, email, name, picture, created_at) "
                "VALUES ('u1', 'u1@local', 'u1', '', 0)"
            )
        )
        for ticker in ("RF_cdb_1", "PETR4"):
            conn.execute(
                text(
                    "INSERT INTO portfolio "
                    "(user_id, ticker, quantity, avg_price, category, created_at, updated_at) "
                    "VALUES ('u1', :t, 1, 1000, 'auto', 0, 0)"
                ),
                {"t": ticker},
            )

    command.upgrade(config, "head")

    with create_engine(sqlite_url).begin() as conn:
        tickers = {row[0] for row in conn.execute(text("SELECT ticker FROM portfolio"))}

    assert tickers == {"PETR4"}


def test_migration_history_is_linear():
    scripts = ScriptDirectory.from_config(_alembic_config())
    heads = scripts.get_heads()
    assert len(heads) == 1, f"histórico de migração bifurcado: {heads}"


def test_init_db_is_idempotent():
    """O startup chama init_db em todo boot; rodar de novo não pode falhar."""
    init_db()
    init_db()

    assert "alembic_version" in set(inspect(engine).get_table_names())
