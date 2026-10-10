from __future__ import annotations

from decimal import Decimal

import pytest
import sqlalchemy as sa

from datajob import coleta
from datajob.fontes import b3_cotahist
from tests.conftest import TRECHO
from tests.conftest import zipar as _zip


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


def test_troca_de_ticker_continua_a_serie_do_papel(engine, tmp_path):
    texto = TRECHO.read_text(encoding="latin-1")
    antes = texto.replace("PETR4       010PETROBRAS", "PETX4       010PETROBRAS").replace(
        "BRPETRACNPR6", "BRPETXACNPR1"
    )
    _executar(engine, tmp_path, _zip(antes.replace("20261008", "20261007")))
    _executar(engine, tmp_path, _zip(texto))
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO mercado.emissor (codigo, cnpj, metodo) VALUES "
                "('PETR', '33000167000101', 'fca'), ('PETX', '33000167000101', 'fca')"
            )
        )

    with engine.connect() as conn:
        serie = conn.execute(
            sa.text(
                "SELECT data, codigo FROM mercado.cotacao_papel "
                "WHERE cnpj = '33000167000101' AND classe = 'PN' ORDER BY data"
            )
        ).all()

    assert [(str(d), c) for d, c in serie] == [("2026-10-07", "PETX4"), ("2026-10-08", "PETR4")], (
        "VVAR3, VIIA3 e BHIA3 são três ISINs da mesma empresa"
    )


def test_recibo_de_subscricao_fica_fora_da_serie_do_papel(engine, tmp_path):
    texto = TRECHO.read_text(encoding="latin-1")
    petr4 = next(linha for linha in texto.splitlines() if linha[12:24].strip() == "PETR4")
    recibo = petr4[:10] + "10" + "PETR9       " + petr4[24:230] + "BRPETRR09PR1" + petr4[242:]
    linhas = texto.splitlines()
    linhas.insert(-1, recibo)
    linhas[-1] = linhas[-1][:31] + f"{len(linhas) - 2:011d}" + linhas[-1][42:]
    _executar(engine, tmp_path, _zip("\n".join(linhas)))
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO mercado.emissor (codigo, cnpj, metodo) "
                "VALUES ('PETR', '33000167000101', 'fca')"
            )
        )

    assert _um(engine, "SELECT count(*) FROM mercado.cotacao WHERE codigo = 'PETR9'") == 1
    assert (
        _um(
            engine,
            "SELECT string_agg(codigo, ',') FROM mercado.cotacao_papel "
            "WHERE cnpj = '33000167000101' AND classe = 'PN'",
        )
        == "PETR4"
    ), "o recibo tem espécie PN e código BDI 10"
