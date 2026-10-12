from __future__ import annotations

from datetime import date
from decimal import Decimal

import sqlalchemy as sa

from datajob import coleta
from datajob.fontes import tesouro_direto

CSV = (
    "Tipo Titulo;Data Vencimento;Data Base;Taxa Compra Manha;Taxa Venda Manha;PU Compra Manha;"
    "PU Venda Manha;PU Base Manha\n"
    "Tesouro Selic;01/03/2027;09/10/2026;0,01;0,02;20067,61;20056,61;20056,61\n"
    "Tesouro IPCA+;15/08/2024;09/10/2023;0,00;5,49;0,00;3870,12;3866,90\n"
    "Tesouro Selic;01/03/2027;09/10/2026;0,01;0,02;20067,61;20056,61;20056,61\n"
    "Tesouro Selic;;09/10/2026;0,01;0,02;1;1;1\n"
).encode("latin-1")


def test_titulo_fora_de_venda_fica_sem_taxa_de_compra():
    linhas, rejeitadas = tesouro_direto.interpretar(CSV)

    ipca = next(linha for linha in linhas if linha["titulo"] == "Tesouro IPCA+")
    assert ipca["taxa_compra"] is None and ipca["pu_compra"] is None, (
        "taxa zero sem preço não é taxa"
    )
    assert ipca["taxa_venda"] == Decimal("5.49")
    assert len(linhas) == 2, "a mesma linha repetida conta uma vez"
    assert len(rejeitadas) == 1


def test_grava_o_tesouro(engine, tmp_path):
    coleta.executar(
        engine, tmp_path, tesouro_direto.FONTE, tesouro_direto.NOME, CSV, tesouro_direto.processar
    )
    with engine.connect() as conn:
        selic = conn.execute(
            sa.text("SELECT * FROM mercado.tesouro WHERE titulo = 'Tesouro Selic'")
        ).one()

    assert selic.vencimento == date(2027, 3, 1)
    assert selic.pu_base == Decimal("20056.61")
