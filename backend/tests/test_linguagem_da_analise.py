from __future__ import annotations

import re
from datetime import UTC, datetime

import pytest

from app.analysis.decision import decide
from app.analysis.fair_price import (
    RATE_BASE_AVERAGE,
    TechnicalSnapshot,
    ValuationRates,
    compute_fair_price,
)
from app.analysis.falsifiers import falsifiers
from app.analysis.texto import numero, pct, reais

REF = datetime(2026, 9, 23, 15, tzinfo=UTC)

TAXAS = ValuationRates(
    discount_rate=0.145, fii_yield=0.095, rate_base=RATE_BASE_AVERAGE, selic_pct=9.5
)

SIGLAS = {
    "ROE": "retorno sobre o patrimônio",
    "P/VP": "valor patrimonial",
    "P/L": "preço sobre lucro",
    "LPA": "lucro por ação",
    "VPA": "valor patrimonial",
    "RSI": "força relativa",
    "DY": "dividendos",
    "BDR": "recibo de ação",
    "ETF": "fundo",
    "FII": "fundo",
    "Selic": "juro",
    "IPCA": "inflação",
    "CDI": "juro",
}

JARGAO_PROIBIDO = {
    "DCF": "o nome do método é o que ele mede, 'pelo lucro distribuível'",
    "Bazin": "o nome do método é o que ele mede, 'pelos dividendos'",
    "Gordon": "fórmula não é leitura",
    "payout": "é 'a parte do lucro que a empresa distribui'",
    "yield": "é 'rendimento'",
    "insumo": "é 'dado'",
    "exercício": "é 'ano fechado'",
    "normaliz": "é 'a média'",
    "capitaliz": "é 'transformar a distribuição em valor'",
    "taxa de desconto": "é 'taxa exigida', o nome que a tela usa",
}

ALTA = TechnicalSnapshot(
    sma_50=11.0,
    sma_200=9.0,
    rsi_14=74.0,
    trend="uptrend",
    last_price=10.0,
    distance_from_52w_high_pct=-2.0,
    distance_from_52w_low_pct=30.0,
    trend_basis="long",
)

QUEDA = TechnicalSnapshot(
    sma_50=9.0,
    sma_200=11.0,
    rsi_14=22.0,
    trend="downtrend",
    last_price=10.0,
    distance_from_52w_high_pct=-30.0,
    distance_from_52w_low_pct=2.0,
    trend_basis="short",
)


def _anos(valores: list[float], inicio: int = 2021) -> list[dict]:
    return [{"date": f"{inicio + i}-06-01", "value": v} for i, v in enumerate(valores)]


def _acao(**kw):
    base = {
        "price": 10.0,
        "eps": 1.0,
        "book_value": 8.0,
        "dividends": _anos([0.5] * 5),
        "asset_type": "br_stock",
        "net_income_history": [120.0, 120.0, 120.0],
        "equity_history": [800.0, 800.0, 800.0],
        "net_income_ttm": 120.0,
        "rates": TAXAS,
        "reference": REF,
        "pb_ratio": 0.9,
        "desired_yield": 0.06,
    }
    base.update(kw)
    return compute_fair_price(**base)


def _fii(simbolo: str, preco: float, **kw):
    base = {
        "price": preco,
        "eps": None,
        "book_value": 100.0,
        "dividends": _anos([10.0] * 5),
        "asset_type": "fii",
        "rates": TAXAS,
        "reference": REF,
        "symbol": simbolo,
        "pb_ratio": 0.9,
    }
    base.update(kw)
    return compute_fair_price(**base)


CENARIOS = {
    "ação abaixo da faixa": (lambda: _acao(price=5.0), ALTA, 5.0),
    "ação dentro da faixa": (lambda: _acao(price=7.5), QUEDA, 7.5),
    "ação acima da faixa": (lambda: _acao(price=14.0), ALTA, 14.0),
    "ação com lucro curto": (
        lambda: _acao(price=3.0, net_income_history=[120.0, 120.0], equity_history=[800.0, 800.0]),
        None,
        3.0,
    ),
    "ação que cresce destruindo valor": (
        lambda: _acao(price=7.0, equity_history=[1100.0] * 3, dividends=_anos([0.2] * 5)),
        None,
        7.0,
    ),
    "ação sem juro": (lambda: _acao(rates=None), None, 10.0),
    "ação sem retorno sobre o patrimônio": (
        lambda: _acao(net_income_history=None, equity_history=None),
        None,
        10.0,
    ),
    "ação com lucro e lucro por ação em sinais opostos": (
        lambda: _acao(net_income_ttm=-50.0),
        None,
        10.0,
    ),
    "ação com pouco dividendo": (lambda: _acao(dividends=_anos([0.1] * 2)), None, 10.0),
    "FII de tijolo": (lambda: _fii("HGLG11", 90.0), ALTA, 90.0),
    "FII de papel": (lambda: _fii("MXRF11", 120.0), QUEDA, 120.0),
    "FII com corte": (
        lambda: _fii("HGLG11", 90.0, dividends=_anos([10, 10, 10, 10, 3])),
        None,
        90.0,
    ),
    "BDR": (lambda: _acao(asset_type="bdr"), ALTA, 10.0),
    "ETF": (lambda: _acao(asset_type="etf"), None, 10.0),
    "sem cotação": (lambda: _acao(price=None), None, None),
}


def _frases(nome: str) -> list[str]:
    fabrica, tecnico, preco = CENARIOS[nome]
    fair = fabrica()
    dec = decide(fair, tecnico, current_price=preco, avg_cost=8.0 if preco else None)
    return [
        *dec.reasons,
        *(f["condition"] for f in falsifiers(fair, dec.verdict, preco, dec.basis)),
        *(m["note"] for m in fair.methods if m.get("note")),
        *fair.quality_reasons,
    ]


@pytest.mark.parametrize("nome", CENARIOS)
def test_sigla_nunca_chega_sozinha(nome):
    for frase in _frases(nome):
        for sigla, explicacao in SIGLAS.items():
            if not re.search(rf"(?<![\w/]){re.escape(sigla)}(?![\w/])", frase):
                continue
            assert explicacao in frase.lower() or explicacao in frase, (
                f"'{sigla}' chega à tela sem '{explicacao}' ao lado, e metade do público é "
                f"iniciante: {frase}"
            )


@pytest.mark.parametrize("nome", CENARIOS)
def test_jargao_de_analista_nao_chega_a_tela(nome):
    for frase in _frases(nome):
        for termo, troca in JARGAO_PROIBIDO.items():
            assert termo.lower() not in frase.lower(), f"'{termo}' {troca}: {frase}"


@pytest.mark.parametrize("nome", CENARIOS)
def test_numero_da_frase_sai_em_portugues(nome):
    for frase in _frases(nome):
        assert not re.search(r"R\$ ?\d+\.\d{2}(?!\d)", frase), (
            f"R$ 7.41 se lê como setecentos e quarenta e um reais: {frase}"
        )
        assert not re.search(r"\d\.\d+ ?%", frase), f"percentual com ponto: {frase}"


def test_os_cenarios_cobrem_o_que_a_frase_pode_dizer():
    todas = " ".join(f for nome in CENARIOS for f in _frases(nome))

    for trecho in (
        "abaixo do piso",
        "dentro da faixa",
        "acima do teto",
        "crescer consome valor",
        "fundo é de papel",
        "evidência frágil",
        "Sem cotação",
        "Não há preço justo",
        "sinais opostos",
        "O preço vem caindo",
        "O preço caiu rápido",
    ):
        assert trecho in todas, f"sem cenário que diga '{trecho}', a regra de linguagem não o vê"


def test_o_formatador_fala_portugues():
    assert reais(1234.5) == "R$ 1.234,50"
    assert pct(0.145) == "14,5%"
    assert pct(0.2, 0) == "20%"
    assert numero(0.9) == "0,90"


def test_a_primeira_razao_e_a_leitura_e_a_conta_vem_depois():
    fair = _acao(price=5.0)
    dec = decide(fair, ALTA, current_price=5.0)

    assert dec.reasons[0].startswith("O preço está"), (
        "a evidência que a tela mostra aberta são as três primeiras razões: a primeira diz onde "
        "o preço está"
    )
    detalhe = next(i for i, r in enumerate(dec.reasons) if r.startswith("Na conta"))
    assert detalhe >= 3, (
        "as premissas do modelo são método, e o método fica na gaveta do nível Essencial: "
        "entre as três primeiras razões, elas empurravam para fora o que o iniciante lê"
    )
