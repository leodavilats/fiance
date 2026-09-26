from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.analysis.decision import decide
from app.analysis.fair_price import (
    RATE_BASE_AVERAGE,
    RATE_SHOCK,
    ValuationRates,
    compute_fair_price,
    earnings_value,
)
from app.analysis.falsifiers import falsifiers

REF = datetime(2026, 9, 23, 15, tzinfo=UTC)

D = 0.145

TAXAS = ValuationRates(discount_rate=D, fii_yield=0.095, rate_base=RATE_BASE_AVERAGE, selic_pct=9.5)


def _anos(valores: list[float], inicio: int = 2021) -> list[dict]:
    return [{"date": f"{inicio + i}-06-01", "value": v} for i, v in enumerate(valores)]


def _acao(roe: float = 0.15, dividendo: float = 0.5, **kw):
    lucro = 120.0
    base = {
        "price": 10.0,
        "eps": 1.0,
        "book_value": 8.0,
        "dividends": _anos([dividendo] * 5) if dividendo else [],
        "asset_type": "br_stock",
        "net_income_history": [lucro] * 3,
        "equity_history": [lucro / roe] * 3,
        "net_income_ttm": lucro,
        "rates": TAXAS,
        "reference": REF,
    }
    base.update(kw)
    return compute_fair_price(**base)


def _cenarios(r) -> dict[str, float]:
    p = r.premises
    roe, g, q = p["roe"], p["growth"], p["distributable"]
    return {
        "com_alta": earnings_value(1.0, q, g, D + RATE_SHOCK, roe),
        "sem_alta": earnings_value(1.0, 1.0, 0.0, D + RATE_SHOCK, roe),
        "com_baixa": earnings_value(1.0, q, g, D - RATE_SHOCK, roe),
        "sem_baixa": earnings_value(1.0, 1.0, 0.0, D - RATE_SHOCK, roe),
    }


class TestCenarioSemCrescimento:
    def test_quem_nao_cresce_distribui_todo_o_lucro(self):
        r = _acao()

        assert r.premises["value_without_growth"] == pytest.approx(
            earnings_value(1.0, 1.0, 0.0, D, 0.15), abs=0.01
        ), (
            "reter lucro sem crescer é destruir o que foi retido: pela identidade g = ROE × "
            "retenção, crescimento zero é retenção zero"
        )

    def test_sem_dividendo_o_piso_nao_e_so_o_valor_terminal(self):
        r = _acao(dividendo=0.0)
        so_terminal = earnings_value(1.0, 0.0, 0.0, D + RATE_SHOCK, 0.15)

        assert r.fair_low > 1.5 * so_terminal, (
            "com payout zero, o piso antigo zerava o fluxo explícito e sobrava só o terminal: a "
            "faixa media a penalidade de reter sem crescer, e não a incerteza da premissa"
        )


class TestFaixaCobreOsDoisCenarios:
    @pytest.mark.parametrize(("roe", "dividendo"), [(0.15, 0.5), (0.30, 0.3), (0.06, 0.3)])
    def test_piso_e_teto_sao_os_extremos_dos_dois_cenarios(self, roe, dividendo):
        r = _acao(roe=roe, dividendo=dividendo)
        c = _cenarios(r)

        assert r.fair_low == pytest.approx(min(c["com_alta"], c["sem_alta"]), abs=0.01)
        assert r.fair_high == pytest.approx(max(c["com_baixa"], c["sem_baixa"]), abs=0.01)
        assert r.fair_low < r.consensus < r.fair_high, (
            "piso ≤ com(d+1) < com(d) = central < com(d−1) ≤ teto: a ordem vale nos dois regimes"
        )

    def test_quando_crescer_consome_valor_o_teto_e_distribuir_tudo(self):
        r = _acao(roe=0.06, dividendo=0.3)
        c = _cenarios(r)

        assert r.premises["growth_creates_value"] is False
        assert r.fair_high == pytest.approx(c["sem_baixa"], abs=0.01), (
            "com ROE abaixo da taxa, o crescimento que a empresa compra retendo lucro vale menos "
            "que o lucro retido: sem crescimento deixa de ser o cenário pessimista"
        )

    def test_quando_crescer_cria_valor_o_piso_e_nao_crescer(self):
        r = _acao(roe=0.30, dividendo=0.3)

        assert r.premises["growth_creates_value"] is True
        assert r.fair_low == pytest.approx(_cenarios(r)["sem_alta"], abs=0.01)


class TestRazaoEPremissaDeCrescimento:
    def test_a_razao_diz_quando_crescer_consome_valor(self):
        dec = decide(_acao(roe=0.06, dividendo=0.3), current_price=10.0)

        assert any("crescer consome valor" in m for m in dec.reasons)

    def test_a_razao_nao_fala_disso_quando_crescer_cria_valor(self):
        dec = decide(_acao(roe=0.30, dividendo=0.3), current_price=10.0)

        assert not any("crescer consome valor" in m for m in dec.reasons)

    def test_sem_criar_valor_o_crescimento_nao_e_premissa_que_derruba(self):
        r = _acao(roe=0.06, dividendo=0.3)
        preco = (r.consensus + r.fair_high) / 2
        r = _acao(roe=0.06, dividendo=0.3, price=preco)
        metricas = {f["metric"] for f in falsifiers(r, decide(r).verdict, preco)}

        assert "growth" not in metricas, (
            "se o crescimento não se confirmar, aqui o valor sobe: dizer que ele cairia seria "
            "falsificador que não falsifica"
        )
