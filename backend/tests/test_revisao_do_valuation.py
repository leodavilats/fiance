from __future__ import annotations

import math
from datetime import UTC, datetime

import pytest

from app.analysis.decision import (
    BASIS_BAND,
    BASIS_NONE,
    LABELS,
    MOS_BUY,
    MOS_SELL,
    decide,
)
from app.analysis.fair_price import (
    RATE_BASE_AVERAGE,
    TechnicalSnapshot,
    ValuationRates,
    compute_fair_price,
    earnings_value,
)
from app.analysis.falsifiers import falsifiers, price_at_margin

REF = datetime(2026, 9, 23, tzinfo=UTC)

TAXAS = ValuationRates(
    discount_rate=0.145, fii_yield=0.095, rate_base=RATE_BASE_AVERAGE, selic_pct=9.5
)

ALTA_FORTE = TechnicalSnapshot(
    sma_50=110.0,
    sma_200=90.0,
    rsi_14=55.0,
    trend="uptrend",
    last_price=100.0,
    distance_from_52w_high_pct=-2.0,
    distance_from_52w_low_pct=30.0,
    trend_basis="long",
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


def _preco_para_margem(fair, margem: float) -> float:
    return price_at_margin(fair.fair_low, fair.fair_high, margem)


class TestGrahamNaoDefineBorda:
    def test_um_centavo_nao_atravessa_bandas(self):
        antes = _acao(price=12.00)
        depois = _acao(price=12.01)

        assert (antes.fair_low, antes.fair_high) == (depois.fair_low, depois.fair_high)
        assert decide(antes).verdict == decide(depois).verdict, (
            "com Graham na faixa, R$ 12,00 era Manter e R$ 12,01 Vender com urgência: o "
            "filtro de P/VP 1,5 removia o método e a faixa encolhia"
        )

    def test_a_faixa_nao_depende_do_preco(self):
        barato = _acao(price=3.0)
        caro = _acao(price=30.0)

        assert (barato.fair_low, barato.fair_high) == (caro.fair_low, caro.fair_high), (
            "a aplicabilidade de um método que dependia do preço que ele julgava fazia o "
            "votante que diria caro sumir justamente quando o ativo estava caro"
        )


class TestEtiquetaForteExigeEvidencia:
    def test_prejuizo_com_historico_de_dividendo_nao_tem_preco_justo(self):
        r = _acao(
            price=4.0,
            eps=-0.8,
            dividends=_anos([1.0, 1.0, 0.8, 0.5, 0.0]),
            net_income_history=[-80.0, 50.0, 100.0],
            net_income_ttm=-80.0,
        )
        dec = decide(r, current_price=4.0)

        assert dec.verdict == "UNKNOWN", (
            "o Bazin do histórico dava 'Comprar com convicção' com confiança baixa a uma "
            "empresa em prejuízo que tinha parado de pagar"
        )
        assert dec.label == LABELS["UNKNOWN"]
        assert falsifiers(r, dec.verdict, 4.0, dec.basis) == []

    def test_evidencia_fragil_nunca_e_bem_abaixo(self):
        r = _acao(net_income_history=[120.0, 120.0], equity_history=[800.0, 800.0], roe_pct=15.0)
        preco = _preco_para_margem(r, 0.60)
        r = _acao(
            price=preco,
            net_income_history=[120.0, 120.0],
            equity_history=[800.0, 800.0],
            roe_pct=15.0,
        )
        dec = decide(r, current_price=preco)

        assert r.band_quality == "fragil"
        assert r.margin_of_safety >= 0.30
        assert dec.verdict == "BUY"
        assert dec.band_verdict == "STRONG_BUY"
        assert any("evidência frágil" in m for m in dec.reasons)

    def test_a_confianca_vem_da_qualidade(self):
        firme = decide(_acao(dividends=_anos([0.9] * 5)))
        fragil = decide(_acao(net_income_history=[120.0] * 2, equity_history=[800.0] * 2))

        assert firme.confidence > fragil.confidence


class TestClassesSemMetodo:
    @pytest.mark.parametrize("classe", ["bdr", "etf"])
    def test_sem_metodo_mesmo_com_tendencia_forte(self, classe):
        r = _acao(asset_type=classe, price=100.0)
        dec = decide(r, ALTA_FORTE, current_price=100.0)

        assert dec.verdict == "UNKNOWN"
        assert dec.basis == BASIS_NONE, (
            "ler compra em média móvel quando não há valor fundamental troca de paradigma com "
            "o mesmo vocabulário"
        )
        assert falsifiers(r, dec.verdict, 100.0, dec.basis) == []

    def test_bdr_diz_por_que_nao_tem_preco_justo(self):
        dec = decide(_acao(asset_type="bdr"))

        assert any("reais" in m for m in dec.reasons), (
            "descontar lucro em dólar pela Selic faz todo BDR parecer caro"
        )


class TestMargemSimetrica:
    def test_as_duas_pontas_medem_a_mesma_distancia(self):
        r = _acao()
        abaixo = _acao(price=r.fair_low / 1.5)
        acima = _acao(price=r.fair_high * 1.5)

        assert abaixo.margin_of_safety == pytest.approx(-acima.margin_of_safety, abs=1e-3), (
            "contra o teto, -30% disparava com 23% de distância e +30% exigia 43%"
        )

    def test_a_margem_contra_nunca_passa_de_menos_cem_por_cento(self):
        assert _acao(price=1_000.0).margin_of_safety > -1.0


class TestTecnicoNaoDecide:
    def test_tendencia_e_rsi_nao_mudam_a_leitura(self):
        r = _acao()
        sem = decide(r, None, current_price=10.0)
        com = decide(r, ALTA_FORTE, current_price=10.0)

        assert sem.verdict == com.verdict and sem.confidence == com.confidence
        assert any("contexto" in m for m in com.reasons)


class TestPersonalizacao:
    def test_a_meta_de_renda_muda_o_preco_teto_e_nao_a_faixa(self):
        modesta = _acao(desired_yield=0.05)
        exigente = _acao(desired_yield=0.12)

        assert (modesta.fair_low, modesta.fair_high) == (exigente.fair_low, exigente.fair_high)
        assert exigente.personal_ceiling < modesta.personal_ceiling, (
            "a preferência pessoal definia a borda de uma faixa apresentada como valor; ela "
            "continua visível, como preço-teto da meta"
        )

    def test_a_razao_diz_se_cabe_na_meta(self):
        dec = decide(_acao(price=5.0, desired_yield=0.06), current_price=5.0)

        assert any("Cabe na sua meta de renda" in m for m in dec.reasons)


class TestVocabulario:
    def test_a_etiqueta_descreve_posicao_e_nao_ordem(self):
        for rotulo in LABELS.values():
            assert "Comprar" not in rotulo and "Vender" not in rotulo, (
                "a tela dizia 'não é recomendação de compra' embaixo de 'Comprar com convicção'"
            )

    def test_a_razao_declara_as_premissas(self):
        dec = decide(_acao(), current_price=10.0)

        assert any("taxa exigida de 14.5%" in m for m in dec.reasons)
        assert any("Selic média de 10 anos" in m for m in dec.reasons)


class TestFalsificadores:
    def test_o_gatilho_e_o_preco_das_bandas_vizinhas(self):
        r = _acao(dividends=_anos([0.9] * 5))
        preco = (r.fair_low + r.fair_high) / 2
        r = _acao(price=preco, dividends=_anos([0.9] * 5))
        dec = decide(r, current_price=preco)
        gatilhos = {f["becomes"]: f["threshold"] for f in falsifiers(r, dec.verdict, preco)}

        assert dec.verdict == "HOLD"
        assert gatilhos["BUY"] == pytest.approx(r.fair_low * (1 - MOS_BUY), rel=1e-3)
        assert gatilhos["SELL"] == pytest.approx(r.fair_high / (1 + MOS_SELL), rel=1e-3)

    def test_evidencia_fragil_nao_promete_banda_que_nao_alcanca(self):
        kw = {"net_income_history": [120.0] * 2, "equity_history": [800.0] * 2, "roe_pct": 15.0}
        r = _acao(**kw)
        preco = _preco_para_margem(r, 0.20)
        r = _acao(price=preco, **kw)
        dec = decide(r, current_price=preco)

        assert dec.verdict == "BUY"
        assert "STRONG_BUY" not in {f["becomes"] for f in falsifiers(r, dec.verdict, preco)}

    def test_a_premissa_de_taxa_iguala_o_valor_ao_preco(self):
        r = _acao(price=12.0)
        taxa = next(
            f for f in falsifiers(r, decide(r).verdict, 12.0) if f["metric"] == "discount_rate"
        )
        p = r.premises
        valor = earnings_value(
            p["eps_normalized"], p["distributable"], p["growth"], taxa["threshold"], p["roe"]
        )

        assert taxa["kind"] == "premissa"
        assert valor == pytest.approx(12.0, rel=1e-2)

    def test_a_premissa_de_crescimento_so_aparece_quando_derruba(self):
        r = _acao()
        preco = (r.premises["value_without_growth"] + r.fair_high) / 2
        r = _acao(price=preco)
        metricas = {f["metric"] for f in falsifiers(r, decide(r).verdict, preco)}

        assert "growth" in metricas

    def test_fii_tem_a_premissa_da_distribuicao(self):
        r = compute_fair_price(
            price=80.0,
            eps=None,
            book_value=100.0,
            dividends=_anos([9.5] * 5),
            asset_type="fii",
            rates=TAXAS,
            reference=REF,
        )
        premissa = next(
            f for f in falsifiers(r, decide(r).verdict, 80.0) if f["metric"] == "dividend"
        )

        assert premissa["threshold"] == pytest.approx(9.5 * 80.0 / r.consensus, rel=1e-3)

    def test_sem_faixa_nao_ha_falsificador(self):
        r = _acao(rates=None)

        assert falsifiers(r, "UNKNOWN", 10.0, BASIS_BAND) == []


def test_o_preco_na_margem_e_o_inverso_da_margem():
    r = _acao()
    for margem in (0.30, 0.15, -0.15, -0.30):
        preco = price_at_margin(r.fair_low, r.fair_high, margem)
        assert math.isclose(_acao(price=preco).margin_of_safety, margem, abs_tol=1e-3)
