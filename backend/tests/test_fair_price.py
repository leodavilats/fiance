from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.analysis.fair_price import (
    AGREEMENT_INSIDE,
    EQUITY_RISK_PREMIUM,
    FII_PREMIUM,
    INFLATION_TARGET,
    LONG_RUN_GROWTH,
    MAX_GROWTH,
    PRINCIPAL_DIVIDENDS,
    PRINCIPAL_EARNINGS,
    RATE_BASE_AVERAGE,
    RATE_BASE_CURRENT,
    RATE_SHOCK,
    REAL_RATE_FLOOR,
    ValuationRates,
    bazin_fair_price,
    compute_fair_price,
    compute_technical,
    earnings_value,
    graham_number,
    normalized_eps,
    normalized_roe,
    rates_for_valuation,
    recurring_dividend,
)

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


class TestJuroDeReferencia:
    def test_juro_estimado_nao_desconta_lucro(self):
        assert rates_for_valuation({"selic_anual": 14.4, "source": "estimativa"}) is None, (
            "a estimativa é um número fixo do código: descontar lucro por ela seria inventar a "
            "taxa que decide o preço justo"
        )

    def test_a_media_de_dez_anos_e_a_base_quando_existe(self):
        taxas = rates_for_valuation({"selic_anual": 13.75, "selic_media_10a": 9.5, "source": "bcb"})

        assert taxas.rate_base == RATE_BASE_AVERAGE
        assert taxas.discount_rate == pytest.approx(0.095 + EQUITY_RISK_PREMIUM), (
            "custo de capital é taxa de longo prazo: a Selic de um dia muda todo preço justo a "
            "cada reunião do Copom"
        )

    def test_sem_a_serie_a_selic_do_dia_entra_e_se_declara(self):
        taxas = rates_for_valuation({"selic_anual": 13.75, "source": "bcb_cache_vencido"})

        assert taxas.rate_base == RATE_BASE_CURRENT

    def test_o_yield_do_fii_sai_do_juro_real_de_longo_prazo(self):
        taxas = rates_for_valuation({"selic_anual": 13.75, "selic_media_10a": 9.5, "source": "bcb"})

        assert taxas.fii_yield == pytest.approx(0.095 - INFLATION_TARGET + FII_PREMIUM)

    def test_juro_real_negativo_nao_zera_o_yield_exigido(self):
        taxas = rates_for_valuation({"selic_anual": 2.0, "selic_media_10a": 2.0, "source": "bcb"})

        assert taxas.fii_yield == pytest.approx(REAL_RATE_FLOOR + FII_PREMIUM), (
            "com a Selic abaixo da inflação, o yield exigido ia a zero e todo FII valia infinito"
        )


class TestLucroNormalizado:
    def test_a_escala_preserva_a_unidade_do_lpa(self):
        lucro = normalized_eps(4.72, [1.58e9, 1.69e9, 1.37e9], 1.625e9)

        assert lucro.eps == pytest.approx(4.72 * (1.58 + 1.69 + 1.37) / 3 / 1.625, rel=1e-4), (
            "em unit, lucro dividido por número de ações não é o LPA da unit: a escala sai da "
            "razão entre lucros, e o LPA continua na unidade em que a fonte o entrega"
        )

    def test_lucro_extraordinario_nos_12_meses_nao_vira_capacidade(self):
        lucro = normalized_eps(3.0, [100.0, 100.0, 100.0], 300.0)

        assert lucro.eps == pytest.approx(1.0)
        assert lucro.unstable is True

    def test_menos_de_tres_exercicios_usa_o_lpa_de_12_meses(self):
        lucro = normalized_eps(2.0, [100.0, 90.0], 110.0)

        assert lucro.eps == 2.0
        assert lucro.years == 2

    def test_prejuizo_num_dos_anos_marca_instabilidade(self):
        assert normalized_eps(1.0, [100.0, -50.0, 120.0], 100.0).unstable is True

    def test_roe_sai_da_media_de_tres_exercicios(self):
        assert normalized_roe(None, [10.0, 20.0, 30.0], [100.0, 100.0, 100.0]) == 0.2

    def test_patrimonio_negativo_nao_tem_roe(self):
        assert normalized_roe(15.0, [10.0, 10.0, 10.0], [-50.0, -40.0, -30.0]) is None

    def test_sem_serie_o_roe_informado_vale(self):
        assert normalized_roe(18.0, None, None) == 0.18


class TestDividendoRecorrente:
    def test_ano_extraordinario_e_limitado_a_duas_vezes_a_mediana_dos_outros(self):
        d = recurring_dividend(_anos([1.0, 1.0, 1.0, 1.0, 9.0]), reference=REF)

        assert d.capped is True
        assert d.mean == pytest.approx((4 * 1.0 + 2.0) / 5)

    def test_a_guarda_nao_tem_degrau(self):
        abaixo = recurring_dividend(_anos([1.0, 1.0, 1.0, 1.0, 2.9]), reference=REF)
        acima = recurring_dividend(_anos([1.0, 1.0, 1.0, 1.0, 3.1]), reference=REF)

        assert acima.mean == pytest.approx(abaixo.mean), (
            "a regra antiga trocava a série inteira pela mediana acima de 3x: 2,9x inflava o "
            "Bazin em 38%, e 3,1x não mudava nada"
        )

    def test_corte_recente_leva_o_recorrente_ao_ultimo_ano(self):
        d = recurring_dividend(_anos([2.0, 2.0, 2.0, 0.5, 0.3]), reference=REF)

        assert d.cut is True
        assert d.recurring == pytest.approx(0.3), (
            "a média antiga sustentava 4,5x o que o último ano pagava: é a armadilha de "
            "dividendo, e ela saía como barata"
        )

    def test_mudanca_de_politica_para_cima_nao_e_apagada(self):
        d = recurring_dividend(_anos([1.0, 1.0, 1.0, 4.0, 4.0]), reference=REF)

        assert d.recurring > 1.0, (
            "trocar a série pela mediana lia dois anos de política nova como ruído e voltava ao "
            "patamar antigo"
        )

    def test_sem_ano_completo_usa_os_ultimos_12_meses(self):
        d = recurring_dividend(
            [{"date": "2026-03-10", "value": 0.5}, {"date": "2026-06-10", "value": 0.5}],
            reference=REF,
        )

        assert d.recurring == 1.0
        assert d.complete_years == 0

    def test_ano_sem_pagamento_dentro_da_serie_conta_como_zero(self):
        d = recurring_dividend(_anos([6.0, 0.0, 6.0], inicio=2023), reference=REF)

        assert d.mean == pytest.approx(4.0)


class TestModeloDeLucro:
    def test_o_piso_e_o_teto_cercam_o_valor_central(self):
        r = _acao()

        assert r.fair_low < r.consensus < r.fair_high
        assert r.principal == PRINCIPAL_EARNINGS

    def test_o_crescimento_sai_do_roe_e_do_que_a_empresa_retem(self):
        r = _acao()

        assert r.premises["roe"] == pytest.approx(0.15)
        assert r.premises["payout"] == pytest.approx(0.5)
        assert r.premises["growth"] == pytest.approx(0.15 * 0.5), (
            "crescimento de receita não é crescimento de lucro; o que sustenta o lucro "
            "crescendo é o retorno sobre o que a empresa deixa de distribuir"
        )

    def test_o_crescimento_tem_teto(self):
        r = _acao(dividends=[], net_income_history=[800.0] * 3, net_income_ttm=800.0)

        assert r.premises["growth"] == MAX_GROWTH

    def test_so_se_desconta_o_que_pode_ser_distribuido(self):
        tudo = earnings_value(1.0, 1.0, 0.075, 0.145, 0.15)
        distribuivel = earnings_value(1.0, 1 - 0.075 / 0.15, 0.075, 0.145, 0.15)

        assert distribuivel < tudo, (
            "somar o lucro inteiro e ainda crescer por reinvestimento conta duas vezes o lucro "
            "retido"
        )

    def test_crescer_so_cria_valor_quando_o_roe_passa_da_taxa(self):
        taxa = 0.145
        assert earnings_value(1.0, 0.5, 0.05, taxa, 0.10) < earnings_value(
            1.0, 1.0, 0.0, taxa, 0.10
        )
        assert earnings_value(1.0, 0.5, 0.20, taxa, 0.40) > earnings_value(
            1.0, 1.0, 0.0, taxa, 0.40
        )

    def test_o_multiplo_terminal_sai_da_taxa_e_nao_de_uma_constante(self):
        roe = 0.2

        def pl_terminal(taxa):
            return earnings_value(1.0, 1.0, 0.0, taxa, roe, years=0)

        assert pl_terminal(0.145) == pytest.approx(
            (1 + LONG_RUN_GROWTH) * (1 - LONG_RUN_GROWTH / roe) / (0.145 - LONG_RUN_GROWTH)
        )
        assert pl_terminal(0.20) < 0.75 * pl_terminal(0.145), (
            "o P/L terminal fixo em 15 neutralizava a própria ligação com o juro"
        )

    def test_sem_roe_nao_se_inventa_crescimento(self):
        r = _acao(net_income_history=None, equity_history=None, roe_pct=None)

        assert r.fair_low is None
        assert {m["method"]: m["status"] for m in r.methods}["dcf"] == "sem_dado", (
            "o padrão de 8% quando faltava crescimento era dado inventado entrando na faixa"
        )

    def test_roe_abaixo_do_crescimento_de_longo_prazo_se_abstem(self):
        r = _acao(net_income_history=[20.0] * 3, net_income_ttm=20.0, eps=0.2)

        assert r.fair_low is None
        assert {m["method"]: m["status"] for m in r.methods}["dcf"] == "roe_insuficiente"

    def test_sem_juro_de_referencia_nao_ha_faixa(self):
        r = _acao(rates=None)

        assert r.fair_low is None
        assert {m["method"]: m["status"] for m in r.methods}["dcf"] == "sem_juro"

    def test_prejuizo_normalizado_e_silencio_com_motivo(self):
        r = _acao(eps=-0.5, net_income_history=[-60.0, -50.0, 10.0], net_income_ttm=-60.0)

        assert {m["method"]: m["status"] for m in r.methods}["dcf"] == "lucro_negativo"


class TestConfirmacaoEQualidade:
    def test_o_dividendo_confirma_a_faixa_da_acao(self):
        r = _acao()

        assert r.confirmation["method"] == "bazin"
        assert r.consensus_methods == 2
        assert r.independent_inputs == 2

    def test_quem_distribui_pouco_nao_tem_confirmacao_pelo_dividendo(self):
        r = _acao(dividends=_anos([0.1] * 5))

        assert r.confirmation is None
        assert {m["method"]: m["status"] for m in r.methods}["bazin"] == "pouco_distribuido"
        assert r.band_quality != "firme"

    def test_firme_exige_faixa_estreita_e_confirmacao_dentro(self):
        r = _acao(dividends=_anos([0.9] * 5))

        assert r.confirmation["agreement"] == AGREEMENT_INSIDE
        assert r.band_quality == "firme", r.quality_reasons

    def test_lucro_de_menos_de_tres_exercicios_e_fragil(self):
        r = _acao(net_income_history=[120.0, 120.0], equity_history=[800.0, 800.0], roe_pct=15.0)

        assert r.band_quality == "fragil"

    def test_a_qualidade_diz_o_que_a_definiu(self):
        assert _acao().quality_reasons


class TestFii:
    def test_o_principal_e_a_distribuicao_capitalizada(self):
        r = _fii()

        assert r.principal == PRINCIPAL_DIVIDENDS
        assert r.consensus == pytest.approx(9.5 / TAXAS.fii_yield, rel=1e-3)
        assert r.fair_low == pytest.approx(9.5 / (TAXAS.fii_yield + RATE_SHOCK), rel=1e-3)
        assert r.fair_high == pytest.approx(9.5 / (TAXAS.fii_yield - RATE_SHOCK), rel=1e-3)

    def test_o_vpa_confirma(self):
        r = _fii()

        assert r.confirmation["method"] == "vpa"
        assert r.confirmation["agreement"] == AGREEMENT_INSIDE

    def test_fii_sem_distribuicao_nao_tem_faixa(self):
        assert _fii(dividends=[]).fair_low is None


class TestIndicadores:
    def test_graham_e_indicador_e_nao_borda(self):
        r = _acao(price=5.0)
        graham = next(i for i in r.indicators if i["kind"] == "graham")

        assert graham["value"] == graham_number(1.0, 8.0)
        assert r.fair_high < graham["value"], (
            "o número de Graham é o preço-limite de uma triagem; se definisse a borda, a "
            "faixa voltaria a ter um votante que nunca diz caro"
        )

    def test_o_preco_teto_pessoal_sai_da_meta_declarada(self):
        r = _acao(desired_yield=0.08)

        assert r.personal_ceiling == bazin_fair_price(0.5, 0.08)


class TestRsi:
    def test_o_rsi_de_wilder_lembra_a_queda_de_antes_da_janela(self):
        subida = [100.0 + i for i in range(60)]
        com_queda = (
            subida[:40] + [subida[39] - 20.0] + [subida[39] - 20.0 + i for i in range(1, 20)]
        )

        assert compute_technical(dict(enumerate(subida))).rsi_14 == 100.0
        assert compute_technical(dict(enumerate(com_queda))).rsi_14 < 100.0, (
            "a média simples dos 14 últimos movimentos esquecia a queda e dava 100; a "
            "suavização de Wilder, a das plataformas de gráfico, ainda a carrega"
        )
