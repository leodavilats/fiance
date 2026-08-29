"""Migrações versionadas (Alembic).

O teste que importa aqui não é "a migração roda" — é **a migração produz o
esquema que os modelos descrevem**. A regra do projeto sempre foi "coluna nova
exige uma migração; não basta mexer no model", e até 2026-08-28 ela era cobrada
por prosa: o teste antigo conferia que a cadeia criava oito tabelas nomeadas à
mão, então um campo novo sem migração passava batido.

Agora dois bancos vazios são levantados lado a lado — um pela cadeia, outro por
`Base.metadata` — e comparados tabela por tabela e coluna por coluna. É o mesmo
diff que se faria à mão antes de um deploy, rodando em todo build.
"""

import os
import tempfile

import pytest
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from app.core.database import Base, _alembic_config, engine, init_db
from app.models import db_models  # noqa: F401  (registra os modelos no metadata)


def _config_for(url: str):
    config = _alembic_config()
    config.set_main_option("sqlalchemy.url", url)
    return config


def _url(prefixo: str) -> str:
    caminho = os.path.join(tempfile.mkdtemp(prefix=f"fiance_{prefixo}_"), "mig.db")
    return f"sqlite:///{caminho}"


@pytest.fixture()
def sqlite_url():
    return _url("alembic")


def _tabelas(inspector) -> set[str]:
    return set(inspector.get_table_names()) - {"alembic_version"}


class TestACadeiaBateComOsModelos:
    """A verificação que substituiu a convenção escrita."""

    @pytest.fixture()
    def esquemas(self, sqlite_url):
        """Um banco pela migração, outro pelos modelos."""
        command.upgrade(_config_for(sqlite_url), "head")

        url_modelos = _url("metadata")
        Base.metadata.create_all(create_engine(url_modelos))

        return (
            inspect(create_engine(sqlite_url)),
            inspect(create_engine(url_modelos)),
        )

    def test_as_mesmas_tabelas(self, esquemas):
        migrado, modelado = esquemas

        assert _tabelas(migrado) == _tabelas(modelado)

    def test_as_mesmas_colunas_em_cada_tabela(self, esquemas):
        """O modo de falha que a lista fixa de tabelas não pegava: campo novo no
        modelo, migração esquecida, esquema divergente só em produção."""
        migrado, modelado = esquemas

        divergencias = {}
        for tabela in sorted(_tabelas(migrado) & _tabelas(modelado)):
            na_migracao = {c["name"] for c in migrado.get_columns(tabela)}
            no_modelo = {c["name"] for c in modelado.get_columns(tabela)}
            if na_migracao != no_modelo:
                divergencias[tabela] = {
                    "só na migração": sorted(na_migracao - no_modelo),
                    "só no modelo": sorted(no_modelo - na_migracao),
                }

        assert divergencias == {}

    def test_a_chave_primaria_e_a_mesma(self, esquemas):
        """Chave primária divergente não aparece em contagem de coluna, e é o
        tipo de erro que só quebra na primeira gravação concorrente."""
        migrado, modelado = esquemas

        for tabela in sorted(_tabelas(migrado) & _tabelas(modelado)):
            assert (
                migrado.get_pk_constraint(tabela)["constrained_columns"]
                == modelado.get_pk_constraint(tabela)["constrained_columns"]
            ), tabela


class TestACadeiaRoda:
    def test_upgrade_a_partir_do_vazio(self, sqlite_url):
        command.upgrade(_config_for(sqlite_url), "head")

        assert "users" in _tabelas(inspect(create_engine(sqlite_url)))

    def test_downgrade_e_upgrade_voltam_ao_mesmo_lugar(self, sqlite_url):
        config = _config_for(sqlite_url)
        command.upgrade(config, "head")
        antes = _tabelas(inspect(create_engine(sqlite_url)))

        command.downgrade(config, "base")
        assert _tabelas(inspect(create_engine(sqlite_url))) == set()

        command.upgrade(config, "head")
        assert _tabelas(inspect(create_engine(sqlite_url))) == antes

    def test_o_historico_e_linear(self):
        """Duas cabeças significam que dois ramos criaram migração em paralelo,
        e o upgrade escolhe uma delas em silêncio."""
        heads = ScriptDirectory.from_config(_alembic_config()).get_heads()

        assert len(heads) == 1, f"histórico de migração bifurcado: {heads}"

    def test_init_db_e_idempotente(self):
        """O startup chama `init_db` em todo boot; rodar de novo não pode
        falhar."""
        init_db()
        init_db()

        assert "alembic_version" in set(inspect(engine).get_table_names())
