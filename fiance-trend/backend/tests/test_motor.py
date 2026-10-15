from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from pesquisa import registro
from pesquisa.dados import Base, montar
from pesquisa.hipoteses import Hipotese, momento
from pesquisa.motor import Custos, fins_de_mes, simular
from pesquisa.periodos import Periodo

SEM_CUSTO = Custos(por_lado=0.0, imposto=0.15)


def _base(retornos: dict[str, list[float]], inicio: str = "2005-01-31", cdi: float = 0.0, **extra):
    dias = pd.bdate_range(inicio, periods=len(next(iter(retornos.values()))))
    retorno = pd.DataFrame(retornos, index=dias)
    preco = (1 + retorno.fillna(0)).cumprod() * 10
    preco[retorno.isna()] = np.nan
    salto = extra.get("salto", pd.DataFrame(False, index=dias, columns=retorno.columns))
    return Base(
        retorno=retorno,
        preco_ajustado=preco,
        preco=preco,
        volume=extra.get("volume", pd.DataFrame(1e8, index=dias, columns=retorno.columns)),
        salto=salto,
        cdi=pd.Series(cdi, index=dias),
        nomes=pd.Series({c: c for c in retorno.columns}),
        retrato="teste",
    )


def _periodo(base: Base) -> Periodo:
    return Periodo("teste", base.pregoes[0].date(), base.pregoes[-1].date())


def test_fim_de_mes_e_o_ultimo_pregao_do_mes():
    dias = pd.bdate_range("2005-01-03", "2005-03-15")

    assert sorted(fins_de_mes(dias)) == [pd.Timestamp("2005-01-31"), pd.Timestamp("2005-02-28"),
                                          pd.Timestamp("2005-03-15")]  # fmt: skip


def test_a_carteira_segue_o_retorno_e_nao_gira_sem_motivo():
    base = _base({"A": [0.01] * 25})

    resultado = simular(base, _periodo(base), lambda dia: ["A"], SEM_CUSTO)

    fevereiro = resultado.patrimonio.loc["2005-02-25"]
    assert fevereiro == pytest.approx(100_000 * 1.01**19), "compra no fechamento de 31/01"
    assert all(g == 0 for g in resultado.giro[1:]), "mesma escolha, mesmo peso: nada a negociar"


def test_custo_por_lado_na_compra():
    base = _base({"A": [0.0] * 3})

    resultado = simular(base, _periodo(base), lambda dia: ["A"], Custos(por_lado=0.0025))

    assert resultado.custos_pagos == pytest.approx(100_000 * 0.0025 / 1.0025)
    assert resultado.patrimonio.iloc[-1] == pytest.approx(100_000 / 1.0025)


def test_imposto_sobre_o_ganho_realizado_e_prejuizo_compensa():
    dias = pd.bdate_range("2005-01-31", periods=45)
    a = [0.0] * 45
    b = [0.0] * 45
    a[5] = 0.10
    b[25] = -0.20
    base = _base({"A": a, "B": b})
    escolhas = {pd.Timestamp("2005-01-31"): ["A"], pd.Timestamp("2005-02-28"): ["B"]}

    resultado = simular(base, _periodo(base), lambda dia: escolhas.get(dia, ["A"]), SEM_CUSTO)

    assert dias[-1] >= pd.Timestamp("2005-03-31")
    assert resultado.imposto_pago == pytest.approx(10_000 * 0.15), (
        "ganho de 10% vendido em fevereiro"
    )
    assert resultado.patrimonio.loc["2005-03-31"] == pytest.approx((110_000 - 1_500) * 0.8), (
        "o prejuízo de março fica para compensar adiante, sem devolver imposto"
    )


def test_dia_de_salto_sem_evento_rende_zero():
    salto = pd.DataFrame(False, index=pd.bdate_range("2005-01-31", periods=4), columns=["A"])
    salto.iloc[2] = True
    base = _base({"A": [0.0, 0.0, 2.0, 0.0]}, salto=salto)

    resultado = simular(base, _periodo(base), lambda dia: ["A"], SEM_CUSTO)

    assert resultado.patrimonio.iloc[-1] == pytest.approx(100_000)
    assert resultado.saltos_zerados == 1


def test_papel_que_deixa_de_negociar_vira_caixa_no_fim_do_mes():
    retornos = [0.0, 0.05] + [np.nan] * 23
    base = _base({"A": retornos}, cdi=0.0001)

    resultado = simular(
        base, _periodo(base), lambda dia: ["A"] if dia.month == 1 else [], SEM_CUSTO
    )

    assert resultado.carteiras[pd.Timestamp("2005-02-28")] == []
    assert resultado.patrimonio.iloc[-1] > 105_000 - 750, "vendeu pelo último preço e rendeu CDI"


def test_momento_ignora_o_ultimo_mes():
    dias = 300
    a = [0.001] * dias
    b = [0.0] * dias
    b[-5] = 0.5
    base = _base({"A": a, "B": b}, inicio="2005-01-03")

    pontos = momento.pontuar(base, base.pregoes[-1], olhar=252, pular=21)

    assert pontos["A"] > pontos["B"], "o salto de B está no mês que a regra ignora"


def test_universo_exige_volume_e_ausencia_de_salto():
    dias = pd.bdate_range("2005-01-03", periods=300)
    volume = pd.DataFrame({"A": 1e8, "B": 1e6, "C": 1e8}, index=dias)
    salto = pd.DataFrame(False, index=dias, columns=["A", "B", "C"])
    salto.loc[dias[-10], "C"] = True
    base = _base({"A": [0.0] * 300, "B": [0.0] * 300, "C": [0.0] * 300}, inicio="2005-01-03",
                 volume=volume, salto=salto)  # fmt: skip

    escolhidos = momento.escolher(base, dias[-1], {"olhar": 252, "pular": 21, "quantidade": 5})

    assert escolhidos == ["A"]


def test_montar_a_partir_do_retrato():
    serie = pd.DataFrame(
        {
            "cnpj": ["1", "1"],
            "classe": ["ON", "ON"],
            "data": [date(2024, 1, 2), date(2024, 1, 3)],
            "codigo": ["AAAA3", "AAAA3"],
            "fechamento": [10.0, 11.0],
            "fechamento_ajustado": [10.0, 11.0],
            "retorno_total": [None, 0.1],
            "volume": [1e7, 1e7],
            "salto_sem_evento": [None, False],
        }
    )
    cdi = pd.DataFrame({"data": [date(2024, 1, 2)], "valor": [0.04]})

    base = montar(serie, cdi, "2026-10-10")

    assert base.nomes["1:ON"] == "AAAA3"
    assert base.cdi.iloc[0] == pytest.approx(0.0004), "o BCB publica a taxa em % ao dia"
    assert base.cdi.iloc[1] == 0.0


def _hipotese(congelada: bool) -> Hipotese:
    return Hipotese("teste", "teste", lambda b, d, p: [], {"x": 1}, congelada=congelada)


def test_prova_so_abre_para_hipotese_congelada(tmp_path):
    with pytest.raises(registro.ProvaLacrada, match="congelada"):
        registro.conferir_prova(_hipotese(False), forcar=False, arquivo=tmp_path / "r.jsonl")


def test_prova_abre_uma_vez(tmp_path):
    arquivo = tmp_path / "r.jsonl"
    hipotese = _hipotese(True)
    registro.conferir_prova(hipotese, forcar=False, arquivo=arquivo)
    registro.anotar(hipotese, "prova", "2026-10-10", {}, arquivo=arquivo)

    with pytest.raises(registro.ProvaLacrada, match="já foi aberta"):
        registro.conferir_prova(hipotese, forcar=False, arquivo=arquivo)
    registro.conferir_prova(hipotese, forcar=True, arquivo=arquivo)


def test_registro_conta_as_variacoes(tmp_path):
    arquivo = tmp_path / "r.jsonl"
    for x in (1, 2, 2):
        h = Hipotese("teste", "teste", lambda b, d, p: [], {"x": x})
        registro.anotar(h, "estudo", "2026-10-10", {}, arquivo=arquivo)

    assert registro.tentativas("teste", arquivo=arquivo) == 2


def test_relatorio_mostra_a_execucao_e_a_curva(tmp_path):
    from pesquisa import relatorio

    base = _base({"A": [0.01] * 25})
    resultado = simular(base, _periodo(base), lambda dia: ["A"], SEM_CUSTO)
    hipotese = _hipotese(False)
    arquivo = tmp_path / "r.jsonl"
    registro.anotar(hipotese, "estudo", "teste", {"retorno_anual": 0.1, "excesso_anual": -0.02},
                    arquivo=arquivo)  # fmt: skip
    relatorio.guardar(resultado, hipotese.nome, registro.assinatura(hipotese), "estudo", base.nomes,
                      pasta=tmp_path)  # fmt: skip

    pagina = relatorio.gerar(arquivo, tmp_path)

    assert "<polyline" in pagina
    assert "-2,0%" in pagina
    assert "<li>A</li>" in pagina


def test_teto_recusa_a_nona_variacao_e_aceita_repetir(tmp_path):
    arquivo = tmp_path / "r.jsonl"
    for x in range(registro.TETO_DO_ESTUDO):
        registro.anotar(Hipotese("h", "h", lambda b, d, p: [], {"x": x}), "estudo", "t", {},
                        arquivo=arquivo)  # fmt: skip

    nova = Hipotese("h", "h", lambda b, d, p: [], {"x": 99})
    with pytest.raises(registro.TetoAtingido):
        registro.conferir_teto(nova, forcar=False, arquivo=arquivo)
    registro.conferir_teto(Hipotese("h", "h", lambda b, d, p: [], {"x": 0}), False, arquivo)
    registro.conferir_teto(nova, forcar=True, arquivo=arquivo)


def test_filtro_de_tendencia_vai_para_o_cdi_com_o_mercado_em_queda():
    from pesquisa.hipoteses import momento_tendencia

    dias = 500
    subindo = _base({"A": [0.001] * dias, "B": [0.002] * dias}, inicio="2005-01-03")
    caindo = _base({"A": [-0.001] * dias, "B": [-0.002] * dias}, inicio="2005-01-03")
    parametros = dict(momento_tendencia.MOMENTO_TENDENCIA.parametros, quantidade=1)

    assert momento_tendencia.escolher(subindo, subindo.pregoes[-1], parametros) == ["B"]
    assert momento_tendencia.escolher(caindo, caindo.pregoes[-1], parametros) == []


def test_rebalanceamento_trimestral_so_mexe_no_fim_do_trimestre():
    base = _base({"A": [0.0] * 140, "B": [0.0] * 140}, inicio="2005-01-03")
    escolhas = []

    simular(base, _periodo(base), lambda dia: escolhas.append(dia) or ["A"], SEM_CUSTO,
            meses_entre_rebalanceamentos=3)  # fmt: skip

    assert [d.month for d in escolhas] == [3, 6]


def test_giro_mensal_divide_pelos_meses_e_nao_pelos_rebalanceamentos():
    from pesquisa.metricas import resumir

    dias = pd.bdate_range("2005-01-03", periods=140)
    escolhas = {d: (["A"] if d.month < 4 else ["B"]) for d in dias}
    base = _base({"A": [0.0] * 140, "B": [0.0] * 140}, inicio="2005-01-03")

    resultado = simular(base, _periodo(base), lambda dia: escolhas[dia], SEM_CUSTO,
                        meses_entre_rebalanceamentos=3)  # fmt: skip

    assert resumir(resultado)["giro_mensal_medio"] == pytest.approx(3.0 / 6, abs=0.01), (
        "compra em março (1) e troca tudo em junho (2), em seis meses"
    )


def test_baixa_volatilidade_escolhe_o_que_menos_oscila():
    from pesquisa.hipoteses import baixa_volatilidade

    dias = 500
    calmo = [0.002 if i % 2 else 0.0 for i in range(dias)]
    agitado = [0.03 if i % 2 else -0.025 for i in range(dias)]
    base = _base({"1:ON": calmo, "2:ON": agitado}, inicio="2005-01-03")
    parametros = dict(baixa_volatilidade.BAIXA_VOLATILIDADE.parametros, quantidade=1)

    assert baixa_volatilidade.escolher(base, base.pregoes[-1], parametros) == ["1:ON"]


def test_dividendos_escolhe_o_maior_rendimento_entre_quem_tem_historico():
    from pesquisa.hipoteses import dividendos

    dias = 500
    base = _base({"1:ON": [0.001] * dias, "2:ON": [0.001] * dias, "3:ON": [0.001] * dias},
                 inicio="2005-01-03")  # fmt: skip
    provento = pd.DataFrame(0.0, index=base.pregoes, columns=base.retorno.columns)
    provento.iloc[-100, 0] = 1.0
    provento.iloc[-100, 1] = 0.5
    base.provento = provento
    parametros = dict(dividendos.DIVIDENDOS.parametros, quantidade=5)

    assert dividendos.escolher(base, base.pregoes[-1], parametros) == ["1:ON", "2:ON"], (
        "o 3 nunca teve provento na base: é lacuna, não rendimento zero"
    )


def test_mercado_com_filtro_entra_no_indice_e_sai_para_o_cdi():
    from pesquisa.hipoteses import mercado_tendencia

    dias = 500
    subindo = _base({"A": [0.001] * dias, "B": [0.003] * dias}, inicio="2005-01-03")
    caindo = _base({"A": [-0.001] * dias, "B": [-0.003] * dias}, inicio="2005-01-03")
    parametros = mercado_tendencia.MERCADO_TENDENCIA.parametros

    assert mercado_tendencia.escolher(subindo, subindo.pregoes[-1], parametros) == [
        "mercado:sintetico"
    ]
    assert subindo.retorno["mercado:sintetico"].iloc[-1] == pytest.approx(0.002)
    assert mercado_tendencia.escolher(caindo, caindo.pregoes[-1], parametros) == []


def test_etf_com_filtro_usa_o_preco_do_etf():
    from pesquisa.hipoteses import mercado_tendencia

    dias = 500
    base = _base({"A": [0.001] * dias, "B": [0.003] * dias}, inicio="2005-01-03")
    base.etf = pd.DataFrame(
        {"data": base.pregoes, "codigo": "PIBB11", "fechamento": 50.0, "fator_cotacao": 1}
    )
    parametros = mercado_tendencia.ETF_TENDENCIA.parametros

    assert mercado_tendencia.escolher_etf(base, base.pregoes[-1], parametros) == ["etf:PIBB11"]
    assert base.retorno["etf:PIBB11"].iloc[-1] == 0.0
