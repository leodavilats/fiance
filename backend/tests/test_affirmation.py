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
        resumo_aporte = QuickInvestService()._resumo(alocacoes, None, "goals", [])

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


METAS_COM_TUDO = {
    "goals": [
        {"category": "renda_fixa", "target_pct": 30.0},
        {"category": "acoes_br", "target_pct": 40.0},
        {"category": "fiis", "target_pct": 30.0},
    ]
}


def _folhas_numericas(valor, caminho=()):
    if isinstance(valor, dict):
        for chave, item in valor.items():
            if chave != "affirmation":
                yield from _folhas_numericas(item, (*caminho, chave))
    elif isinstance(valor, list):
        for item in valor:
            yield from _folhas_numericas(item, caminho)
    elif isinstance(valor, int | float) and not isinstance(valor, bool):
        yield caminho, float(valor)


class TestSubtracao:
    def _aporte(self, client, nivel, valor, uid):
        headers = make_auth_headers(uid)
        client.put("/api/goals", headers=headers, json=METAS_COM_TUDO)
        nivel(valor)
        return client.post(
            "/api/quick-invest", json={"cash_available": 10000}, headers=headers
        ).json()

    def test_o_valor_alocado_nao_sai_por_subtracao(self, client, nivel):
        prescritivo = self._aporte(client, nivel, 3, "u_afirm_subtracao_3")
        analitico = self._aporte(client, nivel, 2, "u_afirm_subtracao_2")

        alocado = prescritivo["allocated_cash"]
        assert alocado and prescritivo["unallocated"] and prescritivo["fixed_income"], (
            "o cenário precisa de alocação, renda fixa e sobra, senão a tentativa não prova nada"
        )
        caixa = analitico["total_cash"]
        assert caixa == prescritivo["total_cash"]

        restante = analitico["remaining_cash"]
        sem_destino = [u["value"] for u in analitico["unallocated"]]
        depois = [b["value"] for b in analitico["portfolio_balance"].values()]
        tentativas = {
            "caixa menos o que ficou em caixa": None if restante is None else caixa - restante,
            "caixa menos o que ficou sem destino": (
                None if None in sem_destino else caixa - sum(sem_destino)
            ),
            "soma do balanço depois do aporte": None if None in depois else sum(depois),
        }
        for tentativa, resultado in tentativas.items():
            assert resultado is None, (
                f"{tentativa} reconstrói o valor de ação que a régua retira no nível 2"
            )

        for caminho, numero in _folhas_numericas(analitico):
            assert abs(numero - alocado) > 0.005, f"{caminho} é o próprio valor alocado"
            assert abs(caixa - numero - alocado) > 0.005, (
                f"caixa menos {caminho} dá o valor alocado"
            )

    def test_nenhuma_cifra_de_acao_sobra_em_outro_campo(self, client, nivel):
        prescritivo = self._aporte(client, nivel, 3, "u_afirm_cifras_3")
        analitico = self._aporte(client, nivel, 2, "u_afirm_cifras_2")

        segredos = {
            prescritivo["remaining_cash"],
            prescritivo["fixed_income"]["amount"],
            *(a["suggested_investment"] for a in prescritivo["allocations"]),
            *(u["value"] for u in prescritivo["unallocated"]),
            *(b["value"] for b in prescritivo["portfolio_balance"].values()),
            *(b["percentage"] for b in prescritivo["portfolio_balance"].values()),
        }
        folhas = {numero for _, numero in _folhas_numericas(analitico)}

        assert not segredos & folhas, (
            "cifra que só existe no nível prescritivo não pode reaparecer em outro campo"
        )

    def test_a_explicacao_do_que_ficou_sem_destino_fica(self, client, nivel):
        analitico = self._aporte(client, nivel, 2, "u_afirm_motivo_2")

        assert analitico["unallocated"], "o fato de sobrar dinheiro é análise, e fica"
        assert all(u["reason"] for u in analitico["unallocated"])
        assert all(b["target"] is not None for b in analitico["portfolio_balance"].values()), (
            "a meta é o que a pessoa declarou, não instrução"
        )


class TestProjecaoDaEstrategia:
    PLANO = {
        "cash_available": 1000.0,
        "total_invested": 5000.0,
        "current_allocation": [{"category": "acoes_br", "current_value": 5000.0}],
        "projected_allocation": [
            {
                "category": "acoes_br",
                "projected_value": 5494.0,
                "projected_pct": 91.5,
                "assets_count": 2,
            }
        ],
    }

    def test_a_projecao_sai_fora_do_nivel_prescritivo(self, nivel):
        projecao = apply(self.PLANO, nivel(2))["projected_allocation"][0]

        assert projecao["projected_value"] is None, (
            "projetado menos atual é o aporte da categoria: sai pela mesma régua do valor"
        )
        assert projecao["projected_pct"] is None
        assert projecao["category"] == "acoes_br"

    def test_no_nivel_prescritivo_a_projecao_fica(self, nivel):
        projecao = apply(self.PLANO, nivel(3))["projected_allocation"][0]

        assert projecao["projected_value"] == 5494.0

    def test_o_escopo_nao_vaza_para_campo_homonimo_fora_dele(self, nivel):
        resultado = apply({"value": 1.0, "unallocated": [{"value": 2.0}]}, nivel(2))

        assert resultado["value"] == 1.0, (
            "`value` só é valor de ação dentro de `unallocated` e do balanço, não em todo lugar"
        )
        assert resultado["unallocated"][0]["value"] is None
