from __future__ import annotations

import io
import os
import zipfile
from decimal import Decimal
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from datajob import coleta
from datajob.config import url_do_banco
from datajob.fontes import b3_cotahist

URL = os.environ.get("DATAJOB_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not URL, reason="DATAJOB_TEST_DATABASE_URL não definida: gravação precisa de Postgres"
)

RAIZ = Path(__file__).resolve().parents[1]
TRECHO = Path(__file__).parent / "fixtures" / "COTAHIST_D08102026_trecho.TXT"


@pytest.fixture
def engine():
    url = url_do_banco(URL)
    motor = sa.create_engine(url)
    with motor.begin() as conn:
        conn.execute(sa.text("DROP SCHEMA IF EXISTS mercado CASCADE"))
    config = Config(str(RAIZ / "alembic.ini"))
    config.set_main_option("script_location", str(RAIZ / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")
    yield motor
    motor.dispose()


def _zip(texto: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as arquivo:
        arquivo.writestr("COTAHIST.TXT", texto.encode("latin-1"))
    return buffer.getvalue()


def _executar(engine, tmp_path, conteudo: bytes, forcar: bool = False) -> coleta.Resultado:
    return coleta.executar(
        engine,
        tmp_path,
        b3_cotahist.FONTE,
        "COTAHIST_D08102026.ZIP",
        conteudo,
        b3_cotahist.processar,
        forcar,
    )


def _um(engine, sql: str):
    with engine.connect() as conn:
        return conn.execute(sa.text(sql)).scalar_one()


def test_grava_cotacao_ativo_e_ticker(engine, tmp_path):
    resultado = _executar(engine, tmp_path, _zip(TRECHO.read_text(encoding="latin-1")))

    assert (resultado.status, resultado.lidas, resultado.gravadas) == ("ok", 7, 5)
    assert _um(engine, "SELECT fechamento FROM mercado.cotacao WHERE codigo = 'PETR4'") == (
        Decimal("55.48")
    )
    assert _um(engine, "SELECT count(*) FROM mercado.ativo") == 5
    assert _um(engine, "SELECT isin FROM mercado.ticker WHERE codigo = 'PETR4'") == "BRPETRACNPR6"
    assert len(list(tmp_path.rglob("*COTAHIST_D08102026.ZIP"))) == 1, "o bruto é guardado"


def test_rodar_de_novo_nao_muda_nenhuma_linha(engine, tmp_path):
    conteudo = _zip(TRECHO.read_text(encoding="latin-1"))
    _executar(engine, tmp_path, conteudo)

    assert _executar(engine, tmp_path, conteudo).status == "pulada"
    assert _executar(engine, tmp_path, conteudo, forcar=True).gravadas == 0, (
        "regravar o mesmo arquivo não pode tocar linha nenhuma"
    )


def test_correcao_da_b3_atualiza_a_cotacao(engine, tmp_path):
    texto = TRECHO.read_text(encoding="latin-1")
    _executar(engine, tmp_path, _zip(texto))

    corrigido = texto.replace(
        "PETR4       010PETROBRAS   PN      N2   R$  0000000005530",
        "PETR4       010PETROBRAS   PN      N2   R$  0000000005531",
    )

    assert _executar(engine, tmp_path, _zip(corrigido)).gravadas == 1
    assert _um(engine, "SELECT abertura FROM mercado.cotacao WHERE codigo = 'PETR4'") == (
        Decimal("55.31")
    )


def test_quarentena_guarda_o_motivo(engine, tmp_path):
    linhas = TRECHO.read_text(encoding="latin-1").splitlines()
    petr4 = next(i for i, linha in enumerate(linhas) if linha[12:24].strip() == "PETR4")
    linhas[petr4] = linhas[petr4][:56] + "0000000000000" + linhas[petr4][69:]

    resultado = _executar(engine, tmp_path, _zip("\n".join(linhas)))

    assert resultado.quarentena == 1
    assert _um(engine, "SELECT motivo FROM mercado.quarentena") == "preço não positivo"
    assert _um(engine, "SELECT count(*) FROM mercado.cotacao WHERE codigo = 'PETR4'") == 0


def test_arquivo_recusado_registra_a_falha_e_nao_grava(engine, tmp_path):
    cortado = "\n".join(TRECHO.read_text(encoding="latin-1").splitlines()[:-1])

    with pytest.raises(b3_cotahist.ArquivoInvalido):
        _executar(engine, tmp_path, _zip(cortado))

    assert _um(engine, "SELECT status FROM mercado.coleta") == "falhou"
    assert _um(engine, "SELECT count(*) FROM mercado.cotacao") == 0


def test_ano_antigo_nao_sobrescreve_o_nome_atual(engine, tmp_path):
    texto = TRECHO.read_text(encoding="latin-1")
    _executar(engine, tmp_path, _zip(texto))

    antigo = texto.replace("20261008", "20151008").replace("PETROBRAS   ", "PETROBRAS AN")
    _executar(engine, tmp_path, _zip(antigo))

    assert _um(engine, "SELECT nome_resumido FROM mercado.ativo WHERE isin = 'BRPETRACNPR6'") == (
        "PETROBRAS"
    )
    assert (
        _um(engine, "SELECT primeiro_pregao::text FROM mercado.ticker WHERE codigo = 'PETR4'")
        == "2015-10-08"
    )
