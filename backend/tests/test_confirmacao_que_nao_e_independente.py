from __future__ import annotations

from datetime import UTC, datetime

from app.analysis.decision import decide
from app.analysis.fair_price import (
    AGREEMENT_FAR,
    RATE_BASE_AVERAGE,
    ValuationRates,
    compute_fair_price,
)

REF = datetime(2026, 9, 23, 15, tzinfo=UTC)

TAXAS = ValuationRates(
    discount_rate=0.145, fii_yield=0.095, rate_base=RATE_BASE_AVERAGE, selic_pct=9.5
)


def _anos(valores: list[float], inicio: int = 2021) -> list[dict]:
    return [{"date": f"{inicio + i}-06-01", "value": v} for i, v in enumerate(valores)]


def _acao_de_payout_baixo(**kw):
    base = {
        "price": 10.0,
        "eps": 1.0,
        "book_value": 8.0,
        "dividends": _anos([0.30] * 5),
        "asset_type": "br_stock",
        "net_income_history": [120.0] * 3,
        "equity_history": [400.0] * 3,
        "net_income_ttm": 120.0,
        "rates": TAXAS,
        "reference": REF,
    }
    base.update(kw)
    return compute_fair_price(**base)


def _fii(**kw):
    base = {
        "price": 100.0,
        "eps": None,
        "book_value": 100.0,
        "dividends": _anos([9.5] * 5),
        "asset_type": "fii",
        "rates": TAXAS,
        "reference": REF,
    }
    base.update(kw)
    return compute_fair_price(**base)


class TestDividendoLongeNaAcao:
    def test_payout_baixo_poe_o_dividendo_longe_da_faixa(self):
        r = _acao_de_payout_baixo()

        assert r.confirmation["agreement"] == AGREEMENT_FAR
        assert r.methods_disagree is True, "a distância continua declarada: ela é um fato"

    def test_longe_por_construcao_alarga_e_nao_derruba(self):
        r = _acao_de_payout_baixo()

        assert r.band_quality == "ampla", (
            "a leitura pelos dividendos usa a mesma taxa e o crescimento do principal, e com "
            "payout baixo fica longe da faixa por construção: frágil sem que nenhum dado discorde "
            "seria rebaixar a evidência pelo formato da fórmula"
        )
        assert any("mesma taxa" in q for q in r.quality_reasons)

    def test_a_etiqueta_forte_volta_a_ser_alcancavel(self):
        r = _acao_de_payout_baixo(price=1.0)

        assert decide(r, current_price=1.0).verdict == "STRONG_BUY"


class TestValorPatrimonialLongeNoFii:
    def test_vpa_longe_da_faixa_segue_fragil(self):
        r = _fii(book_value=40.0)

        assert r.confirmation["agreement"] == AGREEMENT_FAR
        assert r.band_quality == "fragil", (
            "no FII o VPA é insumo independente da distribuição: discordar dela em mais de 30% é "
            "evidência, e não formato da fórmula"
        )
