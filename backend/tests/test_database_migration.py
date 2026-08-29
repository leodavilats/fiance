import os
import tempfile

import pytest
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

from app.core.database import (
    Base,
    RevisaoDesconhecida,
    _alembic_config,
    engine,
    init_db,
)
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
    @pytest.fixture()
    def esquemas(self, sqlite_url):
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

    def test_os_mesmos_tipos_de_coluna(self, esquemas):
        migrado, modelado = esquemas

        divergencias = {}
        for tabela in sorted(_tabelas(migrado) & _tabelas(modelado)):
            na_migracao = {c["name"]: str(c["type"]) for c in migrado.get_columns(tabela)}
            no_modelo = {c["name"]: str(c["type"]) for c in modelado.get_columns(tabela)}
            for nome, tipo in no_modelo.items():
                if nome in na_migracao and na_migracao[nome] != tipo:
                    divergencias[f"{tabela}.{nome}"] = {
                        "migração": na_migracao[nome],
                        "modelo": tipo,
                    }

        assert divergencias == {}

    def test_a_chave_primaria_e_a_mesma(self, esquemas):
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
        heads = ScriptDirectory.from_config(_alembic_config()).get_heads()

        assert len(heads) == 1, f"histórico de migração bifurcado: {heads}"

    def test_init_db_e_idempotente(self):
        init_db()
        init_db()

        assert "alembic_version" in set(inspect(engine).get_table_names())


class TestOPontoDePartidaEConferido:
    @pytest.fixture()
    def banco_migrado(self, sqlite_url, monkeypatch):
        command.upgrade(_config_for(sqlite_url), "head")
        motor = create_engine(sqlite_url)
        monkeypatch.setattr("app.core.database.engine", motor)
        return motor

    def _carimbar(self, motor, revisao):
        with motor.begin() as conexao:
            conexao.execute(text("delete from alembic_version"))
            if revisao is not None:
                conexao.execute(
                    text("insert into alembic_version (version_num) values (:r)"),
                    {"r": revisao},
                )

    def test_revisao_que_nao_existe_mais_diz_qual_e(self, banco_migrado):
        self._carimbar(banco_migrado, "0007_loss_compensable")

        with pytest.raises(RevisaoDesconhecida) as erro:
            init_db()

        assert "0007_loss_compensable" in str(erro.value)

    def test_banco_com_tabelas_e_sem_carimbo_falha_alto(self, banco_migrado):
        self._carimbar(banco_migrado, None)

        with pytest.raises(RevisaoDesconhecida):
            init_db()

    def test_revisao_conhecida_passa(self, banco_migrado):
        (head,) = ScriptDirectory.from_config(_alembic_config()).get_heads()
        self._carimbar(banco_migrado, head)

        init_db()

        assert "users" in _tabelas(inspect(banco_migrado))
