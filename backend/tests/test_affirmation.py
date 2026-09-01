from __future__ import annotations

import pytest

from app.affirmation import Affirmation, Mode, apply, current
from app.core.config import get_settings
from tests.conftest import make_auth_headers


@pytest.fixture()
def nivel(monkeypatch):
    settings = get_settings()

    def _definir(valor, suitability=False):
        monkeypatch.setattr(settings, "affirmation_level", valor, raising=False)
        monkeypatch.setattr(
            settings, "suitability_personalization_allowed", suitability, raising=False
        )
        return current()

    return _definir


# Os nomes aqui são os do payload real das rotas — `suggested_investment` e
# `suggested_quantity` no quick-invest, `invest_amount` na estratégia. Um payload
# sintético com nomes genéricos deixou passar, por um tempo, que a régua não
# alcançava nenhum campo de verdade.
PAYLOAD = {
    "total_cash": 1000.0,
    "allocated_cash": 950.0,
    "summary": "3 ativos selecionados.",
    "allocations": [
        {
            "ticker": "PETR4",
            "amount": 500.0,
            "quantity": 15,
            "current_price": 38.0,
            "suggested_quantity": 13,
            "suggested_investment": 494.0,
            "score": 82,
            "margin_of_safety": 0.31,
            "rationale": "Score alto | MS 31%",
        }
    ],
    "suggestions": [
        {
            "ticker": "BBAS3",
            "price": 28.0,
            "quantity": 17,
            "invest_amount": 476.0,
            "score": 79,
        }
    ],
    "portfolio_balance": {"acoes_br": {"current_pct": 40.0, "target_pct": 60.0}},
}


class TestPadrao:
    def test_o_padrao_e_analitico(self):
        assert current().level is Affirmation.ANALYTICAL

    def test_valor_invalido_cai_no_analitico_e_nao_estoura(self, nivel):
        for valor in ("banana", None, 9, -1, 0):
            assert nivel(valor).level is Affirmation.ANALYTICAL


class TestNivelPrescritivo:
    def test_o_valor_por_ativo_aparece(self, nivel):
        modo = nivel(3)

        resultado = apply(PAYLOAD, modo)

        assert resultado["allocations"][0]["amount"] == 500.0
        assert resultado["allocations"][0]["suggested_investment"] == 494.0
        assert resultado["allocations"][0]["suggested_quantity"] == 13
        assert resultado["suggestions"][0]["invest_amount"] == 476.0
        assert resultado["allocated_cash"] == 950.0

    def test_o_aviso_diz_que_nao_e_recomendacao_personalizada(self, nivel):
        assert "não são recomendação personalizada" in nivel(3).disclaimer.lower()


class TestNivelAnalitico:
    def test_o_valor_por_ativo_sai(self, nivel):
        resultado = apply(PAYLOAD, nivel(2))

        assert resultado["allocations"][0]["amount"] is None
        assert resultado["allocated_cash"] is None

    def test_o_agregado_nao_sai_sozinho(self, nivel):
        """O que instrui é o valor por ativo — reter só o total seria meia régua."""
        resultado = apply(PAYLOAD, nivel(2))
        alocacao = resultado["allocations"][0]

        assert alocacao["suggested_investment"] is None
        assert alocacao["suggested_quantity"] is None
        assert resultado["suggestions"][0]["invest_amount"] is None

    def test_a_analise_que_sustentava_o_numero_fica(self, nivel):
        resultado = apply(PAYLOAD, nivel(2))
        alocacao = resultado["allocations"][0]

        assert alocacao["ticker"] == "PETR4"
        assert alocacao["score"] == 82
        assert alocacao["margin_of_safety"] == 0.31
        assert alocacao["rationale"]
        assert alocacao["current_price"] == 38.0
        assert resultado["suggestions"][0]["price"] == 28.0

    def test_o_estado_da_carteira_fica(self, nivel):
        resultado = apply(PAYLOAD, nivel(2))

        assert resultado["portfolio_balance"]["acoes_br"]["target_pct"] == 60.0

    def test_o_aviso_diz_que_nao_e_recomendacao(self, nivel):
        aviso = nivel(2).disclaimer.lower()

        assert "não é recomendação" in aviso
        assert "não considera a sua situação financeira" in aviso


class TestNivelDescritivo:
    def test_nenhum_ativo_e_apontado(self, nivel):
        resultado = apply(PAYLOAD, nivel(1))

        assert resultado["allocations"] == []

    def test_o_estado_da_carteira_continua(self, nivel):
        resultado = apply(PAYLOAD, nivel(1))

        assert resultado["portfolio_balance"]["acoes_br"]["current_pct"] == 40.0

    def test_o_aviso_diz_que_nao_avalia_ativos(self, nivel):
        assert "não avalia ativos" in nivel(1).disclaimer.lower()


class TestSuitability:
    def test_prescritivo_desliga_personalizacao_por_perfil(self, nivel):
        assert nivel(3, suitability=False).personalized is False

    def test_a_liberacao_e_explicita_e_separada(self, nivel):
        assert nivel(3, suitability=True).personalized is True

    def test_niveis_menores_nao_sao_afetados(self, nivel):
        assert nivel(2).personalized is True
        assert nivel(1).personalized is True


class TestRespostaDaApi:
    def test_toda_resposta_afetada_carrega_o_modo(self, client):
        headers = make_auth_headers("u_afirm_modo")

        corpo = client.post(
            "/api/quick-invest", json={"cash_available": 1000}, headers=headers
        ).json()

        assert corpo["affirmation"]["level"] == 2
        assert corpo["affirmation"]["disclaimer"]

    def test_o_plano_de_estrategia_tambem_carrega(self, client):
        headers = make_auth_headers("u_afirm_plano")

        corpo = client.get("/api/strategy", headers=headers).json()

        assert "affirmation" in corpo

    def test_rebalanceamento_com_carteira_vazia_tambem_carrega(self, client):
        headers = make_auth_headers("u_afirm_vazio")

        corpo = client.get("/api/rebalance-suggestions", headers=headers).json()

        assert "affirmation" in corpo

    def test_ligar_o_nivel_3_e_so_uma_variavel(self, client, nivel):
        headers = make_auth_headers("u_afirm_switch")

        nivel(3)
        prescritivo = client.post(
            "/api/quick-invest", json={"cash_available": 1000}, headers=headers
        ).json()

        nivel(2)
        analitico = client.post(
            "/api/quick-invest", json={"cash_available": 1000}, headers=headers
        ).json()

        assert prescritivo["affirmation"]["prescriptive"] is True
        assert analitico["affirmation"]["prescriptive"] is False
        assert analitico["allocated_cash"] is None


class TestEstruturalNaoTextual:
    def test_o_resumo_nao_e_reescrito(self, nivel):
        resultado = apply(PAYLOAD, nivel(2))

        assert resultado["summary"] == PAYLOAD["summary"]

    def test_a_prosa_nao_carrega_a_cifra_que_a_regua_retira(self):
        """A régua retira campo e não reescreve texto.

        Enquanto o resumo dizia "sugerimos investir R$ 950,00", o valor retido em
        `allocated_cash`/`invest_amount` reaparecia duas linhas abaixo, na prosa.
        Quem gera resumo aqui não pode citar cifra de aporte.
        """
        from app.analysis.strategy import _generate_strategy_summary
        from app.models.quick_invest import QuickInvestAllocation
        from app.services.quick_invest_service import QuickInvestService

        alocacoes = [
            QuickInvestAllocation(
                ticker="PETR4",
                name="Petrobras",
                category="acoes_br",
                sector="Energia",
                current_price=38.0,
                suggested_quantity=13,
                suggested_investment=494.0,
                rationale="Score alto",
                score=82.0,
                dividend_yield=12.0,
            )
        ]
        resumo_aporte = QuickInvestService()._build_summary(alocacoes)

        resumo_estrategia = _generate_strategy_summary(
            {"type": "Moderado"},
            [{"category": "acoes_br", "invest_amount": 494.0}],
            [{"category": "fiis", "gap_value": 7000.0, "gap_pct": 7.0}],
        )

        for resumo in (resumo_aporte, resumo_estrategia):
            assert "R$" not in resumo
            assert "494" not in resumo

    def test_o_modo_e_um_dado_e_nao_um_ramo_de_codigo(self):
        modo = Mode(
            level=Affirmation.ANALYTICAL,
            disclaimer="x",
            prescriptive=False,
            asset_level=True,
            personalized=True,
        )

        assert apply({"amount": 10}, modo)["amount"] is None
