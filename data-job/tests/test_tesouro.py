from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

import pytest
import sqlalchemy as sa

from datajob import coleta
from datajob.erros import ArquivoInvalido
from datajob.fontes import tesouro_direto

CSV = (
    "Tipo Titulo;Data Vencimento;Data Base;Taxa Compra Manha;Taxa Venda Manha;PU Compra Manha;"
    "PU Venda Manha;PU Base Manha\n"
    "Tesouro Selic;01/03/2027;09/10/2026;0,01;0,02;20067,61;20056,61;20056,61\n"
    "Tesouro IPCA+;15/08/2024;09/10/2023;0,00;5,49;0,00;3870,12;3866,90\n"
    "Tesouro Selic;01/03/2027;09/10/2026;0,01;0,02;20067,61;20056,61;20056,61\n"
    "Tesouro Selic;;09/10/2026;0,01;0,02;1;1;1\n"
).encode("latin-1")


def _titulo(nome, isin, vencimento, taxa_compra, pu_compra, taxa_venda, pu_venda):
    return {
        "treasuryBondName": nome,
        "isinCode": isin,
        "maturityDate": f"{vencimento}T00:00",
        "lastMarketPricingDate": "2026-10-09T18:00:08.193",
        "investmentProfitabilityIndexerName": taxa_compra,
        "unitaryInvestmentValue": pu_compra,
        "redemptionProfitabilityFeeIndexerName": taxa_venda,
        "unitaryRedemptionValue": pu_venda,
    }


SELIC = _titulo(
    "Tesouro Selic 2027", "BR1", "2027-03-01", "SELIC + 0,01%", 20067.61, "SELIC + 0,02%", 20056.61
)
IPCA = _titulo(
    "Tesouro IPCA+ 2032", "BR2", "2032-08-15", "IPCA + 6,72%", 3278.12, "IPCA + 6,84%", 3256.93
)
PREFIXADO = _titulo("Tesouro Prefixado 2027", "BR3", "2027-01-01", "13,47%", 0, "13,47%", 977.19)
SEM_ANO = _titulo("Tesouro Novo", "BR4", "2030-01-01", "1,00%", 1, "1,00%", 1)

SITE = json.dumps(
    {
        "investir": {"TesouroLegado": [SELIC, IPCA]},
        "resgatar": {"TesouroLegado": [SELIC, IPCA, PREFIXADO, SEM_ANO]},
    }
).encode()


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


def test_site_vira_as_mesmas_linhas_do_csv():
    linhas, rejeitadas = tesouro_direto.interpretar_site(SITE)
    por_titulo = {linha["titulo"]: linha for linha in linhas}

    assert set(por_titulo) == {"Tesouro Selic", "Tesouro IPCA+", "Tesouro Prefixado"}, (
        "o nome do site traz o ano de venda; o do CSV, não"
    )
    ipca = por_titulo["Tesouro IPCA+"]
    assert ipca["vencimento"] == date(2032, 8, 15) and ipca["data"] == date(2026, 10, 9)
    assert ipca["taxa_compra"] == Decimal("6.72") and ipca["pu_venda"] == Decimal("3256.93")
    assert por_titulo["Tesouro Selic"]["taxa_venda"] == Decimal("0.02")
    prefixado = por_titulo["Tesouro Prefixado"]
    assert prefixado["taxa_compra"] is None and prefixado["pu_compra"] is None, (
        "título fora de venda fica sem compra, como no CSV"
    )
    assert all(linha["pu_base"] is None for linha in linhas), "o site não publica o PU base"
    assert len(rejeitadas) == 1


def test_site_com_outro_formato_e_recusado():
    with pytest.raises(ArquivoInvalido):
        tesouro_direto.interpretar_site(json.dumps({"investir": {}}).encode())
    with pytest.raises(ArquivoInvalido):
        vazio = {"investir": {"TesouroLegado": []}, "resgatar": {"TesouroLegado": []}}
        tesouro_direto.interpretar_site(json.dumps(vazio).encode())


def test_csv_que_volta_sobrescreve_o_retrato_do_site(engine, tmp_path):
    coleta.executar(
        engine,
        tmp_path,
        tesouro_direto.FONTE_SITE,
        tesouro_direto.nome_do_site(date(2026, 10, 9)),
        SITE,
        tesouro_direto.processar_site,
    )
    coleta.executar(
        engine, tmp_path, tesouro_direto.FONTE, tesouro_direto.NOME, CSV, tesouro_direto.processar
    )
    with engine.connect() as conn:
        selic = conn.execute(
            sa.text(
                "SELECT t.pu_base, c.fonte FROM mercado.tesouro t "
                "JOIN mercado.coleta c ON c.id = t.coleta_id WHERE t.titulo = 'Tesouro Selic'"
            )
        ).one()

    assert selic.fonte == tesouro_direto.FONTE, "o CSV é a fonte principal"
    assert selic.pu_base == Decimal("20056.61")
