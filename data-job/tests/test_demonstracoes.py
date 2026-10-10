from __future__ import annotations

import io
import zipfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
import sqlalchemy as sa

from datajob import coleta, rotina
from datajob.erros import ArquivoInvalido
from datajob.fontes import cvm_demonstracoes

TRECHO = Path(__file__).parent / "fixtures" / "dfp_2024_trecho"

PETROBRAS = "33000167000101"
SO_INDIVIDUAL = "00336701000104"
CPX = "10158356000101"


def _zip(trocas: dict[str, bytes] | None = None) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as arquivo:
        for caminho in sorted(TRECHO.iterdir()):
            arquivo.writestr(caminho.name, (trocas or {}).get(caminho.name, caminho.read_bytes()))
    return buffer.getvalue()


def _linhas(leitura, documento: str, conta: str, demonstracao: str = "DRE"):
    return [
        linha
        for linha in leitura.linhas
        if linha.cnpj == documento and linha.conta == conta and linha.demonstracao == demonstracao
    ]


def test_lucro_e_patrimonio_da_petrobras_em_2024_saem_em_reais():
    leitura = cvm_demonstracoes.interpretar(_zip(), "DFP")

    (lucro,) = _linhas(leitura, PETROBRAS, "3.11.01")
    (patrimonio,) = _linhas(leitura, PETROBRAS, "2.03", "BPP")

    assert lucro.valor == Decimal("36606000000"), "R$ 36,6 bi publicados, em milhares no arquivo"
    assert (lucro.inicio_exercicio, lucro.fim_exercicio) == (date(2024, 1, 1), date(2024, 12, 31))
    assert lucro.consolidado
    assert patrimonio.valor == Decimal("367514000000")
    assert patrimonio.inicio_exercicio == patrimonio.fim_exercicio, "balanço é posição numa data"


def test_so_o_exercicio_corrente_entra():
    leitura = cvm_demonstracoes.interpretar(_zip(), "DFP")

    assert {linha.fim_exercicio.year for linha in leitura.linhas} == {2024}, (
        "o penúltimo é a reapresentação de 2023 dentro do documento de 2024"
    )


def test_individual_so_quando_nao_ha_consolidado():
    leitura = cvm_demonstracoes.interpretar(_zip(), "DFP")
    por_empresa = {
        documento: {linha.consolidado for linha in leitura.linhas if linha.cnpj == documento}
        for documento in (PETROBRAS, SO_INDIVIDUAL)
    }

    assert por_empresa == {PETROBRAS: {True}, SO_INDIVIDUAL: {False}}


def test_linhas_repetidas_e_identicas_viram_uma():
    leitura = cvm_demonstracoes.interpretar(_zip(), "DFP")

    assert len(_linhas(leitura, CPX, "3.01")) == 1, "a CPX publica a mesma conta duas vezes"
    assert leitura.rejeitadas == []


def test_conta_repetida_com_valor_diferente_vai_para_quarentena():
    nome = "dfp_cia_aberta_DRE_con_2024.csv"
    texto = (TRECHO / nome).read_bytes().decode("latin-1")
    linha = next(
        linha
        for linha in texto.splitlines()
        if linha.startswith("33.000.167") and ";ÚLTIMO;" in linha and ";3.01;" in linha
    )
    alterada = linha.replace("490829000.0000000000", "1.0000000000")

    leitura = cvm_demonstracoes.interpretar(
        _zip({nome: (texto + alterada + "\n").encode("latin-1")}), "DFP"
    )

    assert _linhas(leitura, PETROBRAS, "3.01") == []
    assert [r.motivo for r in leitura.rejeitadas] == ["conta repetida com valores diferentes"]


def test_recorte_por_empresa_com_acao():
    leitura = cvm_demonstracoes.interpretar(_zip(), "DFP", com_acao={PETROBRAS})

    assert {linha.cnpj for linha in leitura.linhas} == {PETROBRAS}
    assert len(leitura.documentos) == 3, "o índice entra inteiro: documento é barato"


def test_zip_sem_indice_e_recusado():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as arquivo:
        arquivo.writestr("dfp_cia_aberta_DRE_con_2024.csv", b"")

    with pytest.raises(ArquivoInvalido, match="índice"):
        cvm_demonstracoes.interpretar(buffer.getvalue(), "DFP")


def test_carga_inteira_so_na_primeira_vez():
    assert rotina.anos_de_demonstracao("ITR", False, date(2026, 10, 10))[0] == 2011
    assert rotina.anos_de_demonstracao("DFP", True, date(2026, 10, 10)) == [2025, 2026]


def test_grava_e_regrava_sem_tocar_linha(engine, tmp_path):
    with engine.begin() as conn:
        conn.execute(
            sa.text("INSERT INTO mercado.emissor (codigo, cnpj, metodo) VALUES (:c, :d, 'fca')"),
            [{"c": "PETR", "d": PETROBRAS}, {"c": "CPXD", "d": CPX}],
        )

    def gravar(forcar: bool = False):
        return coleta.executar(
            engine,
            tmp_path,
            cvm_demonstracoes.FONTE["DFP"],
            "dfp_cia_aberta_2024.zip",
            _zip(),
            cvm_demonstracoes.processador("DFP"),
            forcar,
        )

    primeira = gravar()
    assert primeira.gravadas > 0
    assert gravar(forcar=True).gravadas == 0

    with engine.connect() as conn:
        lucro = conn.execute(
            sa.text(
                "SELECT l.valor, d.data_entrega FROM mercado.demonstracao_linha l "
                "JOIN mercado.documento d ON d.id = l.documento_id "
                "WHERE d.cnpj = :c AND l.conta = '3.11.01'"
            ),
            {"c": PETROBRAS},
        ).one()
        empresas = conn.execute(
            sa.text(
                "SELECT DISTINCT d.cnpj FROM mercado.demonstracao_linha l "
                "JOIN mercado.documento d ON d.id = l.documento_id"
            )
        ).scalars()
        assert set(empresas) == {PETROBRAS, CPX}, "sem ação ligada, a empresa fica de fora"
    assert lucro.valor == Decimal("36606000000")
    assert lucro.data_entrega == date(2025, 2, 26), "a data de entrega é o que a pesquisa usa"


def test_visoes_de_fundamento(engine, tmp_path):
    with engine.begin() as conn:
        conn.execute(
            sa.text("INSERT INTO mercado.emissor (codigo, cnpj, metodo) VALUES (:c, :d, 'fca')"),
            [{"c": "PETR", "d": PETROBRAS}, {"c": "XXXX", "d": SO_INDIVIDUAL}],
        )
    coleta.executar(
        engine,
        tmp_path,
        cvm_demonstracoes.FONTE["DFP"],
        "dfp_cia_aberta_2024.zip",
        _zip(),
        cvm_demonstracoes.processador("DFP"),
    )

    with engine.connect() as conn:
        resultado = conn.execute(
            sa.text("SELECT * FROM mercado.fundamento_resultado WHERE cnpj = :c"), {"c": PETROBRAS}
        ).one()
        balanco = conn.execute(
            sa.text("SELECT * FROM mercado.fundamento_balanco WHERE cnpj = :c"), {"c": PETROBRAS}
        ).one()
        individual = conn.execute(
            sa.text("SELECT * FROM mercado.fundamento_resultado WHERE cnpj = :c"),
            {"c": SO_INDIVIDUAL},
        ).one()

    assert resultado.receita == Decimal("490829000000")
    assert resultado.lucro_liquido == Decimal("37009000000")
    assert resultado.lucro_controladores == Decimal("36606000000")
    assert resultado.data_entrega == date(2025, 2, 26)
    assert balanco.patrimonio_liquido == Decimal("367514000000")
    assert balanco.patrimonio_controladores < balanco.patrimonio_liquido, "sem os não controladores"
    assert balanco.divida_bruta > 0
    assert not individual.consolidado
    assert individual.lucro_controladores == individual.lucro_liquido, (
        "sem consolidado não há não controladores: o lucro do período é todo do controlador"
    )
