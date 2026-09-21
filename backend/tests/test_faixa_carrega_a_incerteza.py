from __future__ import annotations

import pytest

from app.analysis.decision import confidence_from_evidence, confidence_label, decide
from app.analysis.fair_price import (
    DCF_FALLBACK_DISCOUNT,
    EQUITY_RISK_PREMIUM,
    compute_fair_price,
    dcf_fair_price,
    discount_rate_from,
    normalized_annual_dividend,
)


def _anos(valores: list[float]) -> list[dict]:
    return [{"date": f"{2021 + i}-03-01", "value": v} for i, v in enumerate(valores)]


class TestDividendoExtraordinarioNaoContamina:
    def test_o_ano_que_destoa_da_propria_serie_e_normalizado(self):
        recorrente, _ = normalized_annual_dividend(_anos([0.5, 0.5, 0.5, 0.5, 0.5]))
        contaminado, ajustou = normalized_annual_dividend(_anos([9.0, 0.5, 0.5, 0.5, 0.5]))

        assert ajustou is True
        assert contaminado == pytest.approx(recorrente), (
            "um pagamento excepcional inflava a média de cinco anos e virava capacidade "
            "recorrente de distribuição"
        )

    @pytest.mark.parametrize("extraordinario", [2.0, 5.0, 9.0, 12.0, 15.0, 30.0])
    def test_a_normalizacao_nao_tem_degrau(self, extraordinario):
        valor, _ = normalized_annual_dividend(_anos([extraordinario, 0.5, 0.5, 0.5, 0.5]))

        assert valor == pytest.approx(0.5), (
            "a guarda antiga só disparava acima de 30% de yield implícito: inflação de 2,8x, "
            "4,4x e 5,6x passava, e a entrada da guarda era um degrau"
        )

    def test_dividendo_que_cresce_nao_e_confundido_com_extraordinario(self):
        valor, ajustou = normalized_annual_dividend(_anos([0.4, 0.5, 0.6, 0.7, 0.8]))

        assert ajustou is False
        assert valor == pytest.approx(0.6), "crescer não é destoar"

    def test_sem_tres_anos_nao_se_declara_o_que_e_recorrente(self):
        _, ajustou = normalized_annual_dividend(_anos([9.0, 0.5]))

        assert ajustou is False


class TestCrescimentoSemDegrau:
    def test_acima_do_teto_o_crescimento_e_limitado_e_nao_zerado(self):
        assert dcf_fair_price(1.0, 26.0) > dcf_fair_price(1.0, 24.0), (
            "crescer 26% valia menos que crescer 24%, porque acima de 25% a premissa voltava "
            "para o padrão de 8%"
        )

    def test_contracao_estagnacao_e_ausencia_sao_distinguidas(self):
        contracao = compute_fair_price(
            price=10.0, eps=1.0, book_value=8.0, dividends=[], revenue_growth_rate=-5.0
        )
        estagnacao = compute_fair_price(
            price=10.0, eps=1.0, book_value=8.0, dividends=[], revenue_growth_rate=0.0
        )
        ausente = compute_fair_price(price=10.0, eps=1.0, book_value=8.0, dividends=[])

        assert contracao.details["growth_source"] == "contracao"
        assert estagnacao.details["growth_source"] == "estagnacao"
        assert ausente.details["growth_source"] == "ausente", (
            "deterioração, estagnação e falta de informação produziam o mesmo número sem que "
            "nada registrasse a diferença"
        )


class TestATaxaDeDescontoSaiDoJuroDoDia:
    def test_a_taxa_acompanha_a_selic(self):
        assert discount_rate_from(15.0) == pytest.approx(0.15 + EQUITY_RISK_PREMIUM), (
            "descontar a 13% fixo com a Selic em 15% é exigir da empresa menos que o título do "
            "governo paga"
        )

    def test_sem_juro_conhecido_cai_no_valor_declarado(self):
        assert discount_rate_from(None) == DCF_FALLBACK_DISCOUNT
        assert discount_rate_from(0.0) == DCF_FALLBACK_DISCOUNT

    def test_juro_mais_alto_derruba_o_preco_justo(self):
        caro = dcf_fair_price(1.0, 8.0, discount_rate=discount_rate_from(10.0))
        barato = dcf_fair_price(1.0, 8.0, discount_rate=discount_rate_from(15.0))

        assert barato < caro


class TestAFaixaDizComOQueSeApoia:
    def _acao(self, **kw):
        base = {
            "price": 10.0,
            "eps": 1.0,
            "book_value": 8.0,
            "dividends": _anos([0.6] * 5),
            "asset_type": "br_stock",
            "revenue_growth_rate": 5.0,
        }
        base.update(kw)
        return compute_fair_price(**base)

    def test_metodos_que_leem_o_mesmo_insumo_nao_contam_duas_vezes(self):
        r = self._acao()

        assert r.consensus_methods == 3
        assert r.independent_inputs == 2, (
            "Graham e lucros descontados vivem do mesmo LPA: se ele estiver errado, os dois "
            "erram juntos, e três métodos são duas evidências"
        )

    def test_bdr_apoiado_num_insumo_so_sai_fragil(self):
        r = compute_fair_price(price=86.0, eps=4.0, book_value=30.0, dividends=[], asset_type="bdr")

        assert r.independent_inputs == 1
        assert r.band_quality == "fragil"

    def test_metodo_unico_e_faixa_de_um_ponto_e_fragil(self):
        r = self._acao(eps=None, book_value=None)

        assert r.fair_low == r.fair_high
        assert r.band_quality == "fragil"

    def test_quem_destoa_e_nomeado_e_nao_apagado(self):
        r = self._acao(dividends=_anos([3.0] * 5))

        destoantes = [m for m in r.methods if m["status"] == "destoa_dos_demais"]
        if not destoantes:
            pytest.skip("este cenário não produziu método destoante")

        assert r.fair_high == max(v for v in (r.bazin, r.graham, r.dcf) if v), (
            "o método que destoa continua na faixa: excluí-lo escondia a discordância que a "
            "faixa existe para mostrar"
        )
        assert r.band_quality == "ampla"

    def test_a_posicao_dentro_da_faixa_e_preservada(self):
        rente_ao_piso = self._acao(price=12.0, dividends=_anos([0.7] * 5))
        rente_ao_teto = self._acao(price=14.2, dividends=_anos([0.7] * 5))

        assert rente_ao_piso.margin_of_safety == rente_ao_teto.margin_of_safety == 0.0
        assert rente_ao_piso.band_position < rente_ao_teto.band_position, (
            "rente ao piso e rente ao teto recebiam margem 0 e viravam a mesma leitura, apesar "
            "de ocuparem posições opostas dentro da faixa"
        )


class TestSilencioComMotivo:
    def test_prejuizo_nao_e_ausencia_de_informacao(self):
        r = compute_fair_price(price=5.0, eps=-1.0, book_value=8.0, dividends=[])

        estados = {m["method"]: m["status"] for m in r.methods}
        assert estados["dcf"] == "lucro_negativo"
        assert estados["graham"] == "lucro_negativo", (
            "prejuízo é informação econômica: tratá-lo como dado ausente apagava o que ele diz"
        )

    def test_metodo_que_nao_descreve_a_classe_se_declara_inaplicavel(self):
        r = compute_fair_price(
            price=100.0, eps=None, book_value=90.0, dividends=_anos([8.0] * 5), asset_type="fii"
        )

        estados = {m["method"]: m["status"] for m in r.methods}
        assert estados["graham"] == "inaplicavel"
        assert estados["vpa"] == "ok"

    def test_dado_ausente_se_distingue_de_dado_reprovado(self):
        sem_dado = compute_fair_price(price=10.0, eps=None, book_value=None, dividends=[])
        reprovado = compute_fair_price(price=40.0, eps=1.0, book_value=1.0, dividends=[])

        assert {m["method"]: m["status"] for m in sem_dado.methods}["graham"] == "sem_dado"
        assert {m["method"]: m["status"] for m in reprovado.methods}["graham"] == "fora_da_faixa"


class TestConfiancaSaiDaEvidencia:
    def _fair(self, **kw):
        r = compute_fair_price(
            price=10.0,
            eps=1.0,
            book_value=8.0,
            dividends=_anos([0.6] * 5),
            asset_type="br_stock",
            revenue_growth_rate=5.0,
        )
        for chave, valor in kw.items():
            setattr(r, chave, valor)
        return r

    def test_faixa_firme_vale_mais_que_faixa_ampla(self):
        firme = confidence_from_evidence(self._fair(band_quality="firme"), "band")
        ampla = confidence_from_evidence(self._fair(band_quality="ampla"), "band")
        fragil = confidence_from_evidence(self._fair(band_quality="fragil"), "band")

        assert firme > ampla > fragil

    def test_leitura_de_tendencia_vale_menos_que_qualquer_faixa(self):
        tendencia = confidence_from_evidence(self._fair(band_quality="sem_faixa"), "trend")
        fragil = confidence_from_evidence(self._fair(band_quality="fragil"), "band")

        assert tendencia < fragil, (
            "recomendar sem referência de valor algum não pode valer o mesmo que recomendar "
            "com uma estimativa fraca"
        )

    def test_a_confianca_sai_em_palavra_e_nao_so_em_decimal(self):
        assert confidence_label(0.7) == "alta"
        assert confidence_label(0.45) == "média"
        assert confidence_label(0.2) == "baixa"

    def test_historico_curto_de_dividendo_reduz_a_confianca(self):
        longo = compute_fair_price(
            price=10.0, eps=None, book_value=None, dividends=_anos([0.6] * 5)
        )
        curto = compute_fair_price(
            price=10.0, eps=None, book_value=None, dividends=_anos([0.6] * 2)
        )

        assert (
            decide(curto, current_price=10.0).confidence
            < decide(longo, current_price=10.0).confidence
        )
