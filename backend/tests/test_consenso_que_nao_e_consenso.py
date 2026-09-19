from __future__ import annotations

from app.analysis.decision import decide
from app.analysis.fair_price import (
    GRAHAM_MAX_PB,
    GRAHAM_MAX_PE,
    MAX_METHOD_DISPERSION,
    compute_fair_price,
    graham_fair_price,
)
from app.analysis.falsifiers import falsifiers


class TestGrahamRespeitaAPropriaFaixa:
    def test_dentro_da_faixa_o_metodo_vale(self):
        preco = 10.0
        eps = 1.0
        vpa = 8.0

        assert preco / eps <= GRAHAM_MAX_PE
        assert preco / vpa <= GRAHAM_MAX_PB

        assert graham_fair_price(eps, vpa, price=preco) is not None

    def test_acima_do_pl_maximo_o_metodo_se_abstem(self):
        preco = 40.0
        eps = 1.0

        assert preco / eps > GRAHAM_MAX_PE
        assert graham_fair_price(eps, 8.0, price=preco) is None, (
            "Graham vale para empresa com P/L até 15 — é o que o glossário promete a quem lê. "
            "Aplicá-lo fora disso produz um preço justo que não descreve a empresa."
        )

    def test_acima_do_pvp_maximo_o_metodo_se_abstem(self):
        assert graham_fair_price(1.0, 1.0, price=10.0, pb_ratio=11.0) is None

    def test_sem_preco_nao_da_para_conferir_a_faixa_e_o_metodo_roda(self):
        assert graham_fair_price(1.0, 8.0) is not None


class TestODcfParticipaDoConsenso:
    def test_acao_que_paga_dividendo_usa_os_tres_metodos(self):
        r = compute_fair_price(
            price=10.0,
            eps=1.0,
            book_value=8.0,
            dividends=[{"date": "2025-03-01", "value": 0.6}],
            asset_type="br_stock",
            revenue_growth_rate=5.0,
        )

        assert r.bazin is not None
        assert r.graham is not None
        assert r.dcf is not None, (
            "o DCF era descartado sempre que havia Bazin, o que deixava o consenso de toda ação "
            "pagadora de dividendo com dividendo e patrimônio, e nenhuma medida de lucro futuro"
        )
        assert r.consensus_methods == 3


class TestConsensoQueNaoEConsenso:
    def _discordante(self):
        return compute_fair_price(
            price=50.0,
            eps=1.5,
            book_value=4.5,
            dividends=[{"date": "2025-03-01", "value": 0.75}],
            asset_type="br_stock",
            revenue_growth_rate=7.0,
        )

    def test_metodos_que_discordam_sao_marcados(self):
        r = self._discordante()

        assert r.method_dispersion is not None
        if r.method_dispersion >= MAX_METHOD_DISPERSION:
            assert r.methods_disagree is True

    def test_quando_discordam_a_faixa_alarga_em_vez_de_calar(self):
        r = compute_fair_price(
            price=100.0,
            eps=10.0,
            book_value=90.0,
            dividends=[{"date": "2025-03-01", "value": 0.1}],
            asset_type="br_stock",
            revenue_growth_rate=20.0,
        )

        if not r.methods_disagree:
            return

        d = decide(r, current_price=100.0)

        assert r.fair_high / r.fair_low >= MAX_METHOD_DISPERSION, (
            "a discordância entre métodos é a largura da faixa: é o que ela mede"
        )
        assert d.verdict != "UNKNOWN", (
            "calar sobre a discordância custava metade das ações sem veredito. A faixa larga já "
            "diz o que a abstenção dizia — que não se sabe o número — sem deixar de ler o preço"
        )
        assert any("faixa" in motivo for motivo in d.reasons), (
            "a faixa larga precisa se explicar, senão vira um número largo sem motivo"
        )

    def test_dentro_da_faixa_nao_ha_margem_a_favor_nem_contra(self):
        r = compute_fair_price(
            price=100.0,
            eps=10.0,
            book_value=90.0,
            dividends=[{"date": "2025-03-01", "value": 0.1}],
            asset_type="br_stock",
            revenue_growth_rate=20.0,
        )

        if r.fair_low is None or not (r.fair_low < 100.0 < r.fair_high):
            return

        assert r.margin_of_safety == 0.0
        assert decide(r, current_price=100.0).verdict == "HOLD"

    def test_a_margem_mede_contra_a_borda_e_nao_contra_a_media(self):
        r = compute_fair_price(
            price=10.0,
            eps=1.0,
            book_value=8.0,
            dividends=[{"date": "2025-03-01", "value": 0.6}],
            asset_type="br_stock",
            revenue_growth_rate=5.0,
        )

        if r.fair_low is None or r.consensus is None:
            return
        if r.margin_of_safety is None or r.margin_of_safety <= 0:
            return

        pela_media = (r.consensus - 10.0) / r.consensus

        assert r.margin_of_safety <= pela_media + 1e-9, (
            "medir contra o piso é mais conservador que medir contra a média, e é essa a razão "
            "de medir contra o piso: comprar exige que o preço esteja abaixo do método mais "
            "pessimista, não da média deles"
        )

    def test_a_abstencao_nao_promete_falsificador(self):
        itens = falsifiers(verdict="UNKNOWN", price=100.0, consensus=80.0)

        assert itens == [], (
            "falsificador de veredito que não existe é promessa que não se pode conferir — "
            "o oposto do que ele existe para ser"
        )

    def test_metodos_que_concordam_produzem_veredito(self):
        r = compute_fair_price(
            price=10.0,
            eps=1.0,
            book_value=8.0,
            dividends=[{"date": "2025-03-01", "value": 0.6}],
            asset_type="br_stock",
            revenue_growth_rate=5.0,
        )

        if r.methods_disagree:
            return

        assert decide(r, current_price=10.0).verdict != "UNKNOWN"

    def test_um_metodo_so_nao_tem_dispersao(self):
        r = compute_fair_price(
            price=10.0,
            eps=None,
            book_value=None,
            dividends=[{"date": "2025-03-01", "value": 0.6}],
            asset_type="etf",
        )

        assert r.consensus_methods == 1
        assert r.method_dispersion is None
        assert r.methods_disagree is False
        assert r.fair_low == r.fair_high, "com um método só, a faixa é um ponto"


class TestARazaoNaoContradizOVeredito:
    def _com_desconto_e_queda(self):
        from app.analysis.fair_price import FairPriceResult, TechnicalSnapshot

        fair = FairPriceResult(
            bazin=None,
            graham=None,
            dcf=None,
            consensus=100.0,
            consensus_methods=2,
            margin_of_safety=0.35,
            fair_low=100.0,
            fair_high=100.0,
            avg_dividend_5y=None,
            dy_12m=None,
            dy_5y=None,
            data_years=0,
            desired_yield_used=0.06,
        )
        tech = TechnicalSnapshot(
            sma_50=90.0,
            sma_200=110.0,
            rsi_14=45.0,
            trend="downtrend",
            trend_basis="long",
            last_price=65.0,
            distance_from_52w_high_pct=None,
            distance_from_52w_low_pct=None,
        )
        return fair, tech

    def test_o_rebaixamento_diz_para_onde_foi(self):
        fair, tech = self._com_desconto_e_queda()

        d = decide(fair, tech, current_price=65.0)

        assert d.verdict == "BUY"
        assert not any("evite entrar" in r.lower() for r in d.reasons), (
            "a tela mostrava a etiqueta Comprar ao lado da frase 'evite entrar contra a "
            "tendência' — duas instruções opostas sobre o mesmo ativo"
        )
        assert any(d.label.lower() in r.lower() for r in d.reasons), (
            "quando o veredito é rebaixado, a razão precisa nomear onde ele foi parar"
        )
