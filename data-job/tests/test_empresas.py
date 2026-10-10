from __future__ import annotations

import io
import json
import zipfile
from datetime import date
from pathlib import Path

import pytest
import sqlalchemy as sa

from datajob import coleta, emissores, rotina
from datajob.emissores import Acao, Empresa
from datajob.erros import ArquivoInvalido
from datajob.fontes import b3_emissores, cvm_cadastro, cvm_fca
from datajob.rede import Ausente, Indisponivel
from tests.conftest import TRECHO, zipar

FIXTURES = Path(__file__).parent / "fixtures"
CADASTRO = (FIXTURES / "cad_cia_aberta_trecho.csv").read_bytes()
VALORES = (FIXTURES / "fca_cia_aberta_valor_mobiliario_2026_trecho.csv").read_bytes()
EMISSORES_B3 = (FIXTURES / "b3_emissores_trecho.json").read_bytes()

PETROBRAS = "33000167000101"
SOUZA_CRUZ = "33009911000139"
BTG = "30306294000145"


def _fca_zip(csv: bytes = VALORES) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as arquivo:
        arquivo.writestr("fca_cia_aberta_valor_mobiliario_2026.csv", csv)
        arquivo.writestr("fca_cia_aberta_2026.csv", b"")
    return buffer.getvalue()


def test_cadastro_guarda_uma_linha_por_cnpj_e_as_canceladas():
    empresas = {e["cnpj"]: e for e in cvm_cadastro.interpretar(CADASTRO)}

    assert len(empresas) == 5, "a Armac aparece duas vezes no cadastro da CVM"
    assert empresas[PETROBRAS]["codigo_cvm"] == "9512"
    assert empresas[SOUZA_CRUZ]["data_cancelamento"] is not None, "quem saiu da bolsa fica"


def test_fca_guarda_ticker_e_ignora_o_mercado_declarado():
    linhas = cvm_fca.interpretar(_fca_zip())
    codigos = {(linha["cnpj"], linha["codigo"]) for linha in linhas}

    assert (PETROBRAS, "PETR4") in codigos
    assert ("04601397000128", "BRST3") in codigos, "a Brisanet declara mercado de balcão"
    assert all(linha["data_referencia"] == date(2026, 1, 1) for linha in linhas)


def test_fca_sem_o_arquivo_de_valores_e_recusado():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as arquivo:
        arquivo.writestr("fca_cia_aberta_2026.csv", b"")

    with pytest.raises(ArquivoInvalido):
        cvm_fca.interpretar(buffer.getvalue())


def test_emissores_da_b3_descartam_cnpj_zero_e_data_sem_listagem():
    linhas = {linha["codigo"]: linha for linha in b3_emissores.interpretar(EMISSORES_B3)}

    assert linhas["BPAC"]["cnpj"] == BTG
    assert linhas["CBTC"]["cnpj"] is None, "ETP estrangeiro vem com CNPJ '0'"
    assert linhas["PETR"]["data_listagem"] is None or linhas["PETR"]["data_listagem"].year < 9999


def test_lista_da_b3_percorre_todas_as_paginas():
    paginas = {
        b3_emissores.url_da_pagina(1): {
            "page": {"totalPages": 2},
            "results": [{"issuingCompany": "PETR"}],
        },
        b3_emissores.url_da_pagina(2): {
            "page": {"totalPages": 2},
            "results": [{"issuingCompany": "BPAC"}],
        },
    }

    conteudo = b3_emissores.baixar_lista(lambda url: json.dumps(paginas[url]).encode())

    assert [e["issuingCompany"] for e in json.loads(conteudo)] == ["BPAC", "PETR"]


def _acao(codigo: str, nome: str, inicio: str = "2010-01-04", fim: str = "2015-12-30") -> Acao:
    return Acao(codigo, nome, date.fromisoformat(inicio), date.fromisoformat(fim))


def _empresa(documento: str, nome: str, registro=None, cancelamento=None) -> Empresa:
    return Empresa(documento, frozenset({nome}), registro, cancelamento)


def test_fca_vence_a_b3_que_vence_o_nome():
    ligados = emissores.ligar(
        [_acao("JBSS", "JBS"), _acao("BPAC", "BTGP BANCO"), _acao("CRUZ", "SOUZA CRUZ")],
        {"JBSS": {"02916265000160"}},
        {"JBSS": "49115815000105", "BPAC": BTG},
        [_empresa(SOUZA_CRUZ, "SOUZA CRUZ S A")],
    )

    assert ligados == {
        "JBSS": ("02916265000160", "fca"),
        "BPAC": (BTG, "b3"),
        "CRUZ": (SOUZA_CRUZ, "nome"),
    }, "o FCA é o CNPJ que entrega os balanços à CVM"


def test_nome_com_dois_candidatos_fica_sem_cnpj():
    ligados = emissores.ligar(
        [_acao("RAIA", "RAIA")],
        {},
        {},
        [_empresa("1", "RAIA DROGASIL S A"), _empresa("2", "RAIA S A")],
    )

    assert ligados == {}


def test_nome_so_casa_com_registro_vigente_no_periodo_de_pregao():
    cancelada_antes = _empresa("1", "SOUZA CRUZ S A", cancelamento=date(2008, 1, 1))

    assert emissores.ligar([_acao("CRUZ", "SOUZA CRUZ")], {}, {}, [cancelada_antes]) == {}


def test_fca_inteiro_so_na_primeira_vez():
    assert rotina.anos_do_fca(False, date(2026, 10, 9))[0] == cvm_fca.PRIMEIRO_ANO
    assert rotina.anos_do_fca(True, date(2026, 10, 9)) == [2025, 2026]


def test_diario_liga_ticker_a_empresa(engine, tmp_path):
    cotahist = TRECHO.read_text(encoding="latin-1")
    respostas = {
        cvm_cadastro.URL: CADASTRO,
        cvm_fca.url_do_ano(2026): _fca_zip(),
        b3_emissores.url_da_pagina(1): json.dumps(
            {"page": {"totalPages": 1}, "results": json.loads(EMISSORES_B3)}
        ).encode(),
        "https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A2026.ZIP": zipar(cotahist),
    }

    def baixar(url: str) -> bytes:
        if url in respostas:
            return respostas[url]
        raise Ausente(url)

    falhas = rotina.diario(engine, tmp_path, baixar, lambda *_: None, hoje=date(2026, 10, 9))

    assert falhas == []
    with engine.connect() as conn:
        ligacao = conn.execute(
            sa.text(
                "SELECT e.razao_social, m.metodo FROM mercado.ativo a "
                "JOIN mercado.emissor m ON m.codigo = substr(a.isin, 3, 4) "
                "JOIN mercado.empresa e ON e.cnpj = m.cnpj WHERE a.isin = 'BRPETRACNPR6'"
            )
        ).one()
    assert ligacao.metodo == "fca"
    assert "PETROBRAS" in ligacao.razao_social.upper()


def test_fonte_fora_do_ar_nao_impede_as_outras(engine, tmp_path):
    def baixar_com_cvm_fora(url: str) -> bytes:
        if "cvm.gov.br" in url:
            raise Indisponivel(f"{url} respondeu 503.")
        if "sistemaswebb3" in url:
            return json.dumps({"page": {"totalPages": 1}, "results": []}).encode()
        raise Ausente(url)

    falhas = rotina.diario(
        engine, tmp_path, baixar_com_cvm_fora, lambda *_: None, hoje=date(2026, 10, 9)
    )

    assert falhas == ["cadastro da CVM", "FCA da CVM", "DFP e ITR da CVM"]


def test_cadastro_regravado_nao_toca_linha(engine, tmp_path):
    def gravar(forcar: bool = False):
        return coleta.executar(
            engine,
            tmp_path,
            cvm_cadastro.FONTE,
            cvm_cadastro.NOME,
            CADASTRO,
            cvm_cadastro.processar,
            forcar,
        )

    assert gravar().gravadas == 5
    assert gravar(forcar=True).gravadas == 0, "o rowcount de lote vinha -1 e escondia isso"
