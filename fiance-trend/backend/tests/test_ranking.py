from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pesquisa.dados import Base
from pesquisa.periodos import Periodo
from pesquisa.ranking import CLASSES, SINAIS, registro
from pesquisa.ranking.medida import avaliar
from pesquisa.ranking.sinais import inclinacao_r2

ACOES = CLASSES["acoes"]


def _base(retorno: pd.DataFrame) -> Base:
    preco = (1 + retorno).cumprod() * 10
    falso = pd.DataFrame(False, index=retorno.index, columns=retorno.columns)
    return Base(
        retorno=retorno,
        preco_ajustado=preco,
        preco=preco,
        volume=pd.DataFrame(1e8, index=retorno.index, columns=retorno.columns),
        salto=falso,
        cdi=pd.Series(0.0, index=retorno.index),
        nomes=pd.Series({c: c for c in retorno.columns}),
        retrato="teste",
    )


def _periodo(base: Base) -> Periodo:
    return Periodo("teste", base.pregoes[0].date(), base.pregoes[-1].date())


def _mercado(deriva: np.ndarray, ruido: float, semente: int = 7) -> pd.DataFrame:
    dias = pd.bdate_range("2005-01-03", periods=252 * 4)
    sorteio = np.random.default_rng(semente).normal(0, ruido, (len(dias), len(deriva)))
    return pd.DataFrame(
        sorteio + deriva, index=dias, columns=[f"P{i:02d}" for i in range(len(deriva))]
    )


def test_tendencia_que_persiste_passa_no_protocolo():
    base = _base(_mercado(np.linspace(-0.001, 0.001, 40), ruido=0.01))

    resumo, meses = avaliar(base, _periodo(base), SINAIS["momento_risco"], ACOES)

    assert resumo["passou"], resumo
    assert resumo["ic"] > 0.1
    assert meses[0]["ativos"] == 40


def test_ruido_nao_passa():
    base = _base(_mercado(np.zeros(40), ruido=0.02))

    resumo, _ = avaliar(base, _periodo(base), SINAIS["momento_risco"], ACOES)

    assert not resumo["passou"], "sem tendência de verdade, o ranking não pode acertar"
    assert abs(resumo["ic"]) < 0.05


def test_mes_com_menos_de_vinte_ativos_nao_entra():
    base = _base(_mercado(np.linspace(-0.001, 0.001, 19), ruido=0.01))

    resumo, meses = avaliar(base, _periodo(base), SINAIS["momento_risco"], ACOES)

    assert meses == [] and not resumo["passou"]


def test_inclinacao_de_reta_perfeita_tem_r2_um():
    dias = pd.bdate_range("2020-01-01", periods=126)
    indice = pd.DataFrame(
        {"reta": np.exp(0.001 * np.arange(126)), "plano": np.ones(126)}, index=dias
    )

    sinal = inclinacao_r2(indice, indice.pct_change(), 125, {"janela": 126})

    assert sinal["reta"] == pytest.approx(0.252)
    assert sinal["plano"] == 0


def _anotar(arquivo, sinal: str, periodo: str, passou: bool, classe: str = "acoes") -> None:
    registro.anotar(
        SINAIS[sinal], CLASSES[classe], periodo, "teste", {"passou": passou}, arquivo=arquivo
    )


def test_validacao_so_abre_depois_de_passar_no_estudo_e_uma_vez(tmp_path):
    arquivo = tmp_path / "registro.jsonl"
    sinal, classe = SINAIS["momento_risco"], ACOES

    with pytest.raises(registro.Recusado):
        registro.conferir(sinal, classe, "validacao", False, arquivo)
    _anotar(arquivo, "momento_risco", "estudo", passou=False)
    with pytest.raises(registro.Recusado):
        registro.conferir(sinal, classe, "validacao", False, arquivo)
    _anotar(arquivo, "momento_risco", "estudo", passou=True)
    registro.conferir(sinal, classe, "validacao", False, arquivo)
    _anotar(arquivo, "momento_risco", "validacao", passou=False)

    with pytest.raises(registro.Recusado, match="já foi aberta"):
        registro.conferir(sinal, classe, "validacao", False, arquivo)
    with pytest.raises(registro.Recusado, match="lacrada"):
        registro.conferir(sinal, classe, "prova", False, arquivo)


def test_teto_de_seis_variacoes_no_estudo(tmp_path):
    arquivo = tmp_path / "registro.jsonl"
    for janela in range(6):
        variacao = SINAIS["momento_risco"].__class__(
            "momento_risco", "", SINAIS["momento_risco"].calcular, {"janela": janela}
        )
        registro.anotar(variacao, ACOES, "estudo", "teste", {"passou": False}, arquivo=arquivo)

    outro = SINAIS["momento_risco"].__class__(
        "outro", "", SINAIS["momento_risco"].calcular, {"janela": 63, "pulo": 0}
    )
    with pytest.raises(registro.Recusado, match="teto"):
        registro.conferir(outro, ACOES, "estudo", False, arquivo)


def test_classe_sem_aceite_nao_roda(tmp_path):
    pendente = CLASSES["fii"].__class__("nova", 1.0, CLASSES["fii"].desde, aceita=False)
    with pytest.raises(registro.Recusado, match="adendo"):
        registro.conferir(SINAIS["momento_risco"], pendente, "estudo", True, tmp_path / "r.jsonl")
