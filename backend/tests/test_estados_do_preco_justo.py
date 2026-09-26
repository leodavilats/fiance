from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.analysis.decision import LABEL_NO_QUOTE, LABELS, decide
from app.analysis.fair_price import (
    RATE_BASE_AVERAGE,
    ValuationRates,
    compute_fair_price,
    normalized_eps,
    recurring_dividend,
)
from app.analysis.falsifiers import price_at_margin

REF = datetime(2026, 9, 23, tzinfo=UTC)

TAXAS = ValuationRates(
    discount_rate=0.145, fii_yield=0.095, rate_base=RATE_BASE_AVERAGE, selic_pct=9.5
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
    }
    base.update(kw)
    return compute_fair_price(**base)


class TestClasseSemModelo:
    @pytest.mark.parametrize("classe", ["renda_fixa", "classe_nova"])
    def test_classe_fora_do_mapa_nao_vira_acao(self, classe):
        r = _acao(asset_type=classe)

        assert r.fair_low is None and r.principal is None, (
            f"{classe} não é ação: descontar o lucro dela seria aplicar a uma classe o modelo de "
            "outra, só porque ela não estava na lista"
        )
        assert {m["status"] for m in r.methods} == {"inaplicavel"}
        assert all(m["note"] for m in r.methods), "silêncio sem motivo não explica nada na tela"

    def test_acao_continua_no_modelo_de_lucro(self):
        assert _acao().fair_low is not None


class TestLucroContraditorio:
    def test_lpa_positivo_com_lucro_negativo_nao_e_normalizado(self):
        lucro = normalized_eps(1.0, [10.0, 10.0, 10.0], -5.0)

        assert lucro.eps is None and lucro.inconsistent is True, (
            "LPA positivo com lucro de 12 meses negativo quer dizer que um dos dois está errado: "
            "usar o LPA bruto produziria preço justo em cima de dado contraditório"
        )

    def test_dado_contraditorio_cala_com_motivo_proprio(self):
        r = _acao(net_income_ttm=-50.0)

        assert r.fair_low is None
        principal = next(m for m in r.methods if m["role"] == "principal")
        assert principal["status"] == "sem_dado", (
            "o status reaproveita um que o aplicativo já traduz: status novo chega cru em "
            "cliente que ainda não atualizou pela loja"
        )
        assert "sinais opostos" in principal["note"]

    def test_lpa_zero_continua_sendo_falta_de_lucro(self):
        r = _acao(eps=0.0)

        principal = next(m for m in r.methods if m["role"] == "principal")
        assert principal["status"] == "lucro_negativo"


class TestAnoCivilBrasileiro:
    def test_a_virada_do_ano_segue_o_fuso_brasileiro(self):
        virada_em_utc = datetime(2027, 1, 1, 1, 0, tzinfo=UTC)
        dividendos = _anos([1.0, 1.0, 1.0, 1.0, 1.0], inicio=2021) + [
            {"date": "2026-12-15", "value": 0.1}
        ]

        r = recurring_dividend(dividendos, reference=virada_em_utc)

        assert r.complete_years == 5 and r.cut is False, (
            "à 1h de 1º de janeiro em UTC ainda são 22h de 31 de dezembro no Brasil: 2026 não é "
            "ano completo, e contá-lo como tal leria a distribuição parcial de dezembro como corte"
        )


class TestFaixaSemCotacao:
    def test_sem_preco_nao_ha_confianca(self):
        fair = _acao(price=None)
        dec = decide(fair, None, current_price=None)

        assert fair.fair_low is not None
        assert dec.verdict == "UNKNOWN"
        assert dec.confidence == 0.0, "confiança numa leitura que não foi feita é número inventado"

    def test_o_rotulo_nao_nega_o_preco_justo_que_existe(self):
        dec = decide(_acao(price=None), None, current_price=None)

        assert dec.label == LABEL_NO_QUOTE != LABELS["UNKNOWN"], (
            "a faixa existe; o que falta é a cotação. 'Sem preço justo' diria o contrário"
        )
        assert any("Sem cotação" in r for r in dec.reasons)

    def test_classe_sem_metodo_continua_sem_preco_justo(self):
        dec = decide(_acao(asset_type="etf"), None, current_price=10.0)

        assert dec.label == LABELS["UNKNOWN"]


class TestBordaDaEtiqueta:
    def test_a_etiqueta_nao_atravessa_a_borda_pelo_arredondamento(self):
        faixa = _acao()
        preco = faixa.fair_low * (1 - 0.29996)
        r = _acao(price=preco)

        assert r.margin_of_safety == 0.3, "o campo exibido continua com quatro casas"
        assert decide(r, None, current_price=preco).band_verdict == "BUY", (
            "a 29,996% do piso a margem ainda não chegou a 30%: arredondar antes de comparar "
            "classificava como 'bem abaixo' um preço acima do gatilho que a própria tela anuncia"
        )

    @pytest.mark.parametrize(("margem", "esperado"), [(0.30, "STRONG_BUY"), (-0.30, "STRONG_SELL")])
    def test_no_preco_do_gatilho_a_etiqueta_ja_mudou(self, margem, esperado):
        faixa = _acao()
        preco = price_at_margin(faixa.fair_low, faixa.fair_high, margem)
        r = _acao(price=preco)

        assert decide(r, None, current_price=preco).band_verdict == esperado, (
            "o gatilho diz 'cair para R$ X ou menos': em R$ X exato a etiqueta já é a nova, e o "
            "ruído de ponto flutuante não pode desfazer isso"
        )
