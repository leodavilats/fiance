from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pesquisa import calibracao, preco_justo
from pesquisa.dados import Base


def _anotar(arquivo, variacao: int, periodo: str, passou: bool) -> None:
    calibracao.anotar(variacao, periodo, "teste", {"passou": passou}, False, arquivo=arquivo)


def test_calibrar_so_existe_se_o_modelo_como_esta_passar(tmp_path):
    arquivo = tmp_path / "r.jsonl"

    with pytest.raises(calibracao.Recusado, match="variação 0"):
        calibracao.conferir(1, "estudo", False, arquivo)
    _anotar(arquivo, 0, "estudo", passou=False)

    with pytest.raises(calibracao.Recusado, match="não repete"):
        calibracao.conferir(0, "estudo", False, arquivo)
    with pytest.raises(calibracao.Recusado, match="variação 0"):
        calibracao.conferir(1, "estudo", False, arquivo)
    with pytest.raises(calibracao.Recusado, match="lacrada"):
        calibracao.conferir(0, "validacao", False, arquivo)


def test_validacao_abre_depois_de_passar_no_estudo(tmp_path):
    arquivo = tmp_path / "r.jsonl"
    _anotar(arquivo, 0, "estudo", passou=True)

    calibracao.conferir(0, "validacao", False, arquivo)
    calibracao.conferir(2, "estudo", False, arquivo)
    with pytest.raises(calibracao.Recusado, match="lacrada"):
        calibracao.conferir(0, "prova", False, arquivo)


def test_parametro_da_variacao_vale_dentro_e_volta_depois():
    modelo = preco_justo.modelo
    antes = (modelo.LONG_RUN_GROWTH, modelo.earnings_value.__defaults__)

    with calibracao.parametros({"LONG_RUN_REAL_GROWTH": 0.02}):
        assert modelo.LONG_RUN_GROWTH == pytest.approx(0.05)
        assert pytest.approx(0.05) in modelo.earnings_value.__defaults__, (
            "o crescimento entra como padrão de argumento: trocar só a constante não muda a conta"
        )

    assert (modelo.LONG_RUN_GROWTH, modelo.earnings_value.__defaults__) == antes


def test_newey_west_desconta_a_sobreposicao():
    rng = np.random.default_rng(3)
    independente = pd.Series(rng.normal(0.02, 0.1, 400))
    sobreposta = independente.rolling(12).mean().dropna()

    t_simples = sobreposta.mean() / (sobreposta.std() / np.sqrt(len(sobreposta)))

    assert preco_justo._t_newey_west(sobreposta, 11) < t_simples / 2


def test_juro_e_a_media_de_dez_anos_e_cala_sem_historia():
    datas = pd.date_range("2000-01-01", periods=180, freq="MS")
    selic = pd.Series(10.0, index=datas)

    juro = preco_justo.juro_na_data(selic, pd.Timestamp("2014-12-31"))

    assert juro.selic_pct == 10.0 and juro.discount_rate == pytest.approx(0.15)
    assert preco_justo.juro_na_data(selic, pd.Timestamp("2004-01-31")) is None


def _base(preco: float) -> Base:
    dias = pd.bdate_range("2012-01-02", "2014-12-31")
    papel = "00000000000001:ON"
    quadro = pd.DataFrame({papel: preco}, index=dias)
    base = Base(
        retorno=quadro * 0,
        preco_ajustado=quadro,
        preco=quadro,
        volume=quadro * 0 + 1e8,
        salto=quadro.astype(bool) & False,
        cdi=pd.Series(0.0, index=dias),
        nomes=pd.Series({papel: "TEST3"}),
        retrato="teste",
    )
    base.acoes = pd.DataFrame(
        {"cnpj": ["00000000000001"], "data": [pd.Timestamp("2012-01-01")], "acoes": [1_000_000]}
    )
    linhas = []
    for ano in range(2009, 2014):
        linhas.append(
            {
                "cnpj": "00000000000001", "tipo": "DFP", "data_referencia": f"{ano}-12-31",
                "versao": 1, "fim_exercicio": f"{ano}-12-31", "receita": 50_000_000.0,
                "lucro_controladores": 10_000_000.0, "patrimonio_controladores": 60_000_000.0,
                "divida_bruta": 0.0, "data_entrega": f"{ano + 1}-03-15",
            }
        )  # fmt: skip
    base.calibracao = {
        "fundamento_app": pd.DataFrame(linhas),
        "provento": pd.DataFrame(
            {
                "cnpj": ["00000000000001"] * 5,
                "classe": ["ON"] * 5,
                "data_com": [f"{a}-06-01" for a in range(2009, 2014)],
                "data_pagamento": [None] * 5,
                "valor": [5.0] * 5,
            }
        ),
        "selic_mensal": pd.DataFrame(
            {"data": pd.date_range("2000-01-01", periods=180, freq="MS"), "valor": 10.0}
        ),
    }
    return base


@pytest.mark.parametrize(("preco", "esperado"), [(20.0, "abaixo"), (1000.0, "acima")])
def test_veredito_sai_do_modelo_do_app_com_o_que_se_sabia(preco, esperado):
    base = _base(preco)
    dados = preco_justo.Dados(base)
    dia = pd.Timestamp("2014-12-31")

    grupo = preco_justo.veredito(
        base, dados, "00000000000001:ON", dia, preco_justo.juro_na_data(dados.selic, dia)
    )

    assert grupo == esperado, "lucro de R$ 10 por ação: R$ 20 é barato, R$ 1.000 é caro"


def test_balanco_entregue_depois_da_data_nao_entra():
    base = _base(20.0)
    dados = preco_justo.Dados(base)

    pacote = preco_justo.pacote_na_data(
        base, dados, "00000000000001:ON", pd.Timestamp("2012-02-29")
    )

    assert {r["data_referencia"] for r in pacote["resultados"]} == {"2009-12-31", "2010-12-31"}, (
        "a DFP de 2011 só foi entregue em mar/2012"
    )


def test_periodos_sao_os_do_protocolo_da_calibracao():
    assert calibracao.PERIODOS["estudo"].inicio.isoformat() == "2011-01-01", (
        "a primeira execução usou o estudo da pesquisa de carteira, de 2005, sem balanço"
    )
    assert calibracao.PERIODOS["prova"].inicio.isoformat() == "2023-01-01"
