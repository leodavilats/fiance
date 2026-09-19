from __future__ import annotations

from app.analysis.decision import BASIS_BAND, BASIS_TREND, decide
from app.analysis.fair_price import (
    TechnicalSnapshot,
    compute_fair_price_inputs,
    fair_price_from_inputs,
)
from app.analysis.falsifiers import falsifiers
from app.services.opportunity_service import OpportunityService, _MarketRecord


def _etf(trend: str = "uptrend", rsi: float = 58.0) -> _MarketRecord:
    return _MarketRecord(
        ticker="BOVA11",
        name="iShares Ibovespa",
        asset_type="etf",
        sector=None,
        price=182.47,
        dividend_yield=None,
        roe=None,
        profit_margin=None,
        debt_to_equity=None,
        revenue_growth=None,
        market_cap=None,
        has_dividend_history=False,
        fair_inputs=compute_fair_price_inputs(
            price=182.47,
            eps=None,
            book_value=None,
            dividends=[],
            asset_type="etf",
        ),
        technical=TechnicalSnapshot(
            sma_50=180.0,
            sma_200=170.0,
            rsi_14=rsi,
            trend=trend,
            trend_basis="long",
            last_price=182.47,
            distance_from_52w_high_pct=-3.0,
            distance_from_52w_low_pct=20.0,
        ),
    )


def _decisao(record: _MarketRecord):
    fair = fair_price_from_inputs(record.fair_inputs)
    return fair, decide(fair, record.technical, current_price=record.price)


class TestOEtfNaoTemFaixa:
    def test_nenhum_metodo_se_aplica(self):
        fair, _ = _decisao(_etf())

        assert fair.consensus_methods == 0
        assert fair.fair_low is None and fair.fair_high is None
        assert fair.margin_of_safety is None, (
            "margem de segurança contra um preço justo que não existe é o número que fazia o ETF "
            "sair com -300% sempre"
        )

    def test_a_leitura_sai_da_tendencia_e_se_declara(self):
        _, dec = _decisao(_etf())

        assert dec.verdict == "BUY"
        assert dec.basis == BASIS_TREND, (
            "veredito de tendência apresentado como se viesse de preço justo é a mesma etiqueta "
            "para duas coisas diferentes"
        )
        assert any("Nenhum método de preço justo" in motivo for motivo in dec.reasons)

    def test_o_que_derruba_a_leitura_e_a_propria_tendencia(self):
        fair, dec = _decisao(_etf())

        itens = falsifiers(
            verdict=dec.verdict,
            price=182.47,
            consensus=fair.consensus,
            fair_low=fair.fair_low,
            fair_high=fair.fair_high,
            basis=dec.basis,
            trend="uptrend",
            rsi_14=58.0,
        )

        assert itens, "era o veredito sem falsificador nenhum que o item 28 descrevia"
        assert all(i["metric"] in ("trend", "rsi") for i in itens)


class TestAsDuasTelasDizemOMesmo:
    def test_o_descobrir_nao_reescreve_o_veredito_da_analise(self):
        record = _etf()
        _, dec = _decisao(record)

        oportunidade = OpportunityService()._build_opportunity(record)

        assert oportunidade.verdict == dec.verdict, (
            "o mesmo ETF saía 'Comprar (momentum)' no Descobrir e 'Sem dados suficientes' na "
            "análise, porque o Descobrir tinha uma régua própria"
        )
        assert oportunidade.label == dec.label
        assert oportunidade.basis == dec.basis

    def test_em_queda_as_duas_telas_tambem_concordam(self):
        record = _etf(trend="downtrend", rsi=45.0)
        _, dec = _decisao(record)

        oportunidade = OpportunityService()._build_opportunity(record)

        assert dec.verdict == "SELL"
        assert oportunidade.verdict == dec.verdict


class TestAcaoContinuaSaindoDaFaixa:
    def test_quem_tem_metodo_nao_cai_na_tendencia(self):
        inputs = compute_fair_price_inputs(
            price=10.0,
            eps=1.0,
            book_value=8.0,
            dividends=[{"date": "2025-03-01", "value": 0.6}],
            asset_type="br_stock",
            revenue_growth_pct=5.0,
        )
        fair = fair_price_from_inputs(inputs)
        tech = TechnicalSnapshot(
            sma_50=9.0,
            sma_200=11.0,
            rsi_14=45.0,
            trend="downtrend",
            trend_basis="long",
            last_price=10.0,
            distance_from_52w_high_pct=None,
            distance_from_52w_low_pct=None,
        )

        dec = decide(fair, tech, current_price=10.0)

        assert dec.basis == BASIS_BAND, (
            "a leitura de tendência é o que sobra quando não há método — não um atalho para "
            "quando há"
        )
