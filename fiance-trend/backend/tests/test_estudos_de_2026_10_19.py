from __future__ import annotations

import pandas as pd
import pytest

from pesquisa import custo_de_troca, filtro_de_risco, taxa_de_desconto


def test_titulo_de_referencia_e_o_mais_longo_a_venda_no_ultimo_dia_do_mes():
    tesouro = pd.DataFrame(
        {
            "data": pd.to_datetime(["2020-03-30", "2020-03-31", "2020-03-31", "2020-03-31"]),
            "titulo": ["Tesouro Prefixado"] * 4,
            "vencimento": pd.to_datetime(["2030-01-01", "2026-01-01", "2029-01-01", "2031-01-01"]),
            "taxa_compra": [8.0, 6.0, 7.0, None],
            "taxa_venda": [8.1, 6.1, 7.1, 7.5],
        }
    )
    assert taxa_de_desconto.titulo_de_referencia(
        tesouro, "Tesouro Prefixado", pd.Timestamp("2020-03-31")
    ) == ("2029-01-01", 7.1), "fora de venda (sem taxa de compra) não é referência"
    assert (
        taxa_de_desconto.titulo_de_referencia(
            tesouro, "Tesouro Prefixado", pd.Timestamp("2020-04-30")
        )
        is None
    ), "mês sem título não herda a taxa de outro mês"


def test_regra_dos_80_vale_para_os_dois_lados():
    def mes(abaixo, dentro, acima):
        return {
            "mes": "2020-01-31",
            **{
                str(c): {
                    "taxa": 0.1,
                    "referencia": None,
                    "contagem": {"abaixo": abaixo, "dentro": dentro, "acima": acima},
                    "largura_mediana": 0.2,
                }
                for c in taxa_de_desconto.CANDIDATAS
            },
        }

    assert not taxa_de_desconto.resumir([mes(1, 1, 18)])["candidatas"]["0"]["compativel"]
    assert not taxa_de_desconto.resumir([mes(17, 2, 1)])["candidatas"]["0"]["compativel"]
    assert taxa_de_desconto.resumir([mes(5, 5, 10)])["candidatas"]["0"]["compativel"]


def test_corwin_schultz_recupera_o_spread_e_respeita_o_dia_invalido():
    maxima = pd.DataFrame({"x": [10.1, 10.1, 10.1, 13.0, 10.1]})
    minima = pd.DataFrame({"x": [10.0, 10.0, 10.0, 12.9, 10.0]})
    valido = pd.DataFrame({"x": [True, True, False, True, True]})
    spread = custo_de_troca.corwin_schultz(maxima, minima, valido)["x"]
    assert spread.iloc[0] == pytest.approx(2 * 0.01 / 2.01), (
        "mesma faixa nos dois dias: S = 2(H/L−1)/(1+H/L)"
    )
    assert pd.isna(spread.iloc[1]) and pd.isna(spread.iloc[2]), "par com dia inválido fica fora"
    assert spread.iloc[3] == 0, "salto entre os dois dias dá spread negativo, que vira zero"
    assert pd.isna(spread.iloc[4]), "o último dia não tem par"


def test_faixa_de_liquidez():
    assert custo_de_troca._faixa(500_000) == "abaixo de 1 mi"
    assert custo_de_troca._faixa(5_000_000) == "5 a 20 mi"
    assert custo_de_troca._faixa(float("nan")) is None


def test_quedas_separam_episodios():
    patrimonio = pd.Series([100, 80, 100, 110, 99, 120, 60, 70])
    assert filtro_de_risco.quedas(patrimonio) == pytest.approx([-0.5, -0.2, -0.1])


def test_julgamento_exige_as_tres_condicoes():
    comprado = {"pior_queda": -0.45, "volatilidade_anual": 0.30, "retorno_anual": 0.05}
    bom = {"pior_queda": -0.25, "volatilidade_anual": 0.18, "retorno_anual": 0.03}
    assert filtro_de_risco.julgar(bom, comprado)["confirmado"]
    caro = {**bom, "retorno_anual": 0.01}
    assert not filtro_de_risco.julgar(caro, comprado)["confirmado"], (
        "perder 4 pontos passa do seguro"
    )
    pouco = {**bom, "pior_queda": -0.31}
    assert not filtro_de_risco.julgar(pouco, comprado)["confirmado"], (
        "cortar menos de um terço não confirma"
    )


def test_estudos_nao_repetem(tmp_path):
    for modulo in (taxa_de_desconto, custo_de_troca, filtro_de_risco):
        arquivo = tmp_path / f"{modulo.__name__}.jsonl"
        modulo.conferir(False, arquivo)
        modulo.anotar("teste", {}, False, arquivo)
        with pytest.raises(modulo.Recusado):
            modulo.conferir(False, arquivo)
        modulo.conferir(True, arquivo)
