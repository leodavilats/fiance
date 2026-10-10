from __future__ import annotations

import pandas as pd
import pytest

from pesquisa.fundamentos import acoes_na_data, na_data, preparar, preparar_acoes
from pesquisa.hipoteses import valor_qualidade
from tests.test_motor import _base

CNPJ = "00000000000191"


def _tabelas():
    resultado = pd.DataFrame(
        [
            ("DFP", "2019-12-31", 80.0, "2020-02-20"),
            ("ITR", "2020-03-31", 20.0, "2020-05-10"),
            ("DFP", "2020-12-31", 100.0, "2021-03-01"),
            ("ITR", "2021-03-31", 30.0, "2021-05-10"),
        ],
        columns=["tipo", "data_referencia", "lucro_controladores", "disponivel_em"],
    ).assign(cnpj=CNPJ, versao=1)
    resultado["fim_exercicio"] = resultado["data_referencia"]
    balanco = resultado[["cnpj", "tipo", "data_referencia", "versao"]].assign(
        patrimonio_controladores=500.0
    )
    return preparar(resultado, balanco)


def _acoes(quantidade: float) -> pd.DataFrame:
    composicao = pd.DataFrame(
        {"cnpj": [CNPJ], "data_referencia": ["2021-03-31"], "acoes_total": [quantidade],
         "tesouraria_total": [0.0]}
    )  # fmt: skip
    capital = pd.DataFrame(
        {"cnpj": [CNPJ, CNPJ], "data_referencia": ["2016-01-01", "2017-01-01"], "versao": [1, 1],
         "data_aprovacao": ["2014-04-02", "2014-04-02"], "acoes_total": [7.0, 7.0]}
    )  # fmt: skip
    return preparar_acoes(composicao, capital)


def test_lucro_de_12_meses_no_trimestre():
    tabela = _tabelas().set_index("data_referencia")

    assert tabela.loc["2020-12-31", "lucro_12m"] == 100
    assert tabela.loc["2021-03-31", "lucro_12m"] == 30 + 100 - 20


def test_so_entra_o_que_ja_tinha_sido_entregue():
    tabela = _tabelas()

    antes = na_data(tabela, pd.Timestamp("2021-04-01"))
    depois = na_data(tabela, pd.Timestamp("2021-06-01"))

    assert antes.loc[CNPJ, "lucro_12m"] == 100, "o ITR de março só sai em maio"
    assert depois.loc[CNPJ, "lucro_12m"] == 110


def test_empresa_que_parou_de_entregar_sai():
    assert na_data(_tabelas(), pd.Timestamp("2023-01-01")).empty


def test_numero_de_acoes_em_milhares_e_corrigido():
    base = _base({f"{CNPJ}:ON": [0.0] * 3}, inicio="2021-06-01")
    base.fundamentos = _tabelas()
    base.acoes = _acoes(0.5)
    dia = base.pregoes[-1]

    tabela = valor_qualidade.pontuar(base, dia, [f"{CNPJ}:ON"])

    assert tabela.loc[f"{CNPJ}:ON", "lucro_sobre_valor"] == pytest.approx(
        110 / (10 * 0.5 * 1000)
    ), "valor de 5 contra patrimônio de 500 é a quantidade em milhares, como a Gafisa declara"
    assert tabela.loc[f"{CNPJ}:ON", "roe"] == pytest.approx(110 / 500)


def test_um_papel_por_empresa_fica_o_mais_negociado():
    volume = pd.DataFrame(
        {f"{CNPJ}:ON": 1e7, f"{CNPJ}:PN": 5e7, "1:ON": 1e7},
        index=pd.bdate_range("2021-01-04", periods=70),
    )
    base = _base({c: [0.0] * 70 for c in volume.columns}, inicio="2021-01-04", volume=volume)

    escolhidos = valor_qualidade.um_papel_por_empresa(base, base.pregoes[-1], list(volume.columns))

    assert escolhidos == [f"{CNPJ}:PN", "1:ON"]


def test_acoes_do_fre_antes_de_2020_e_da_composicao_depois():
    acoes = _acoes(1000.0)

    assert acoes_na_data(acoes, pd.Timestamp("2015-01-01"))[CNPJ] == 7, "aprovado em 2014, pelo FRE"
    assert acoes_na_data(acoes, pd.Timestamp("2021-06-01"))[CNPJ] == 1000
    assert acoes_na_data(acoes, pd.Timestamp("2013-01-01")).empty


def test_quantidade_digitada_errada_sai_e_desdobramento_fica():
    capital = pd.DataFrame(
        {
            "cnpj": [CNPJ] * 5,
            "data_referencia": [
                "2013-01-01",
                "2015-01-01",
                "2016-01-01",
                "2017-01-01",
                "2018-01-01",
            ],
            "versao": [1] * 5,
            "data_aprovacao": [
                "2012-04-01",
                "2014-04-01",
                "2015-04-01",
                "2016-04-01",
                "2017-04-01",
            ],
            "acoes_total": [2865.0, 286.5, 2865.0, 5730.0, 5730.0],
        }
    )
    vazia = pd.DataFrame(columns=["cnpj", "data_referencia", "acoes_total", "tesouraria_total"])

    acoes = preparar_acoes(vazia, capital)

    assert list(acoes["acoes"]) == [2865.0, 2865.0, 5730.0, 5730.0], (
        "o Banco do Brasil de 2015 sai; o desdobramento de 2016 fica"
    )
