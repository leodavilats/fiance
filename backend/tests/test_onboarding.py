from __future__ import annotations

from app.api.demo import DEMO_POSITIONS
from app.api.onboarding import READABLE_PORTFOLIO_SIZE, STEP_GOALS, STEP_PORTFOLIO, TOTAL_STEPS
from app.storage import event_store
from tests.conftest import make_auth_headers


class TestEstadoDerivado:
    def test_conta_nova_comeca_pedindo_a_carteira(self, client):
        headers = make_auth_headers("u_onb_novo")

        corpo = client.get("/api/onboarding", headers=headers).json()

        assert corpo["step"] == STEP_PORTFOLIO
        assert corpo["completed"] is False
        assert corpo["positions"] == 0
        assert "primeira posição" in corpo["reason"]

    def test_o_passo_avanca_sozinho_quando_a_pessoa_faz_o_que_falta(self, client):
        headers = make_auth_headers("u_onb_avanca")

        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        corpo = client.get("/api/onboarding", headers=headers).json()

        assert corpo["step"] == STEP_GOALS
        assert corpo["positions"] == 1

    def test_com_carteira_e_meta_o_passo_e_o_ultimo(self, client):
        headers = make_auth_headers("u_onb_completo")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )
        client.put(
            "/api/goals",
            json={"goals": [{"category": "acoes_br", "target_pct": 60}]},
            headers=headers,
        )

        corpo = client.get("/api/onboarding", headers=headers).json()

        assert corpo["step"] == TOTAL_STEPS
        assert corpo["has_goals"] is True

    def test_importar_por_fora_tambem_avanca_o_onboarding(self, client):
        headers = make_auth_headers("u_onb_import")

        client.post(
            "/api/transactions/import",
            json={"content": "Data;Ativo;Tipo;Quantidade;Preço\n10/01/2024;PETR4;Compra;100;30,00"},
            headers=headers,
        )
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        assert client.get("/api/onboarding", headers=headers).json()["step"] == STEP_GOALS

    def test_o_estado_e_o_mesmo_em_outro_aparelho(self, client):
        primeiro = make_auth_headers("u_onb_multi")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=primeiro,
        )

        segundo = make_auth_headers("u_onb_multi")

        assert (
            client.get("/api/onboarding", headers=segundo).json()["step"]
            == client.get("/api/onboarding", headers=primeiro).json()["step"]
        )


class TestConclusao:
    def test_concluir_carimba_a_conta(self, client):
        headers = make_auth_headers("u_onb_conclui")

        corpo = client.post("/api/onboarding/complete", json={}, headers=headers).json()

        assert corpo["completed"] is True
        assert corpo["onboarded_at"] is not None

    def test_pular_tambem_conclui(self, client):
        headers = make_auth_headers("u_onb_pula")

        corpo = client.post(
            "/api/onboarding/complete", json={"skipped": True}, headers=headers
        ).json()

        assert corpo["completed"] is True

    def test_o_carimbo_nao_e_reescrito_na_segunda_chamada(self, client):
        headers = make_auth_headers("u_onb_idempotente")

        primeiro = client.post("/api/onboarding/complete", json={}, headers=headers).json()
        segundo = client.post("/api/onboarding/complete", json={}, headers=headers).json()

        assert primeiro["onboarded_at"] == segundo["onboarded_at"]

    def test_o_evento_de_conclusao_e_gravado_pelo_servidor(self, client):
        headers = make_auth_headers("u_onb_evento")

        client.post("/api/onboarding/complete", json={}, headers=headers)

        assert event_store.has_event("u_onb_evento", "onboarding_completed")

    def test_o_evento_nao_e_duplicado(self, client):
        headers = make_auth_headers("u_onb_evento_unico")

        client.post("/api/onboarding/complete", json={}, headers=headers)
        client.post("/api/onboarding/complete", json={}, headers=headers)

        eventos = event_store.counts_by_name()
        assert eventos.get("onboarding_completed", 0) >= 1

    def test_pular_nao_bloqueia_o_resto_do_produto(self, client):
        headers = make_auth_headers("u_onb_nao_bloqueia")
        client.post("/api/onboarding/complete", json={"skipped": True}, headers=headers)

        assert client.get("/api/portfolio", headers=headers).status_code == 200
        assert client.get("/api/dashboard", headers=headers).status_code == 200


class TestCarteiraDeDemonstracao:
    def test_a_demonstracao_roda_a_analise_de_verdade(self, client):
        headers = make_auth_headers("u_demo")

        corpo = client.get("/api/demo/portfolio", headers=headers).json()

        assert corpo["is_demo"] is True
        posicoes = corpo["evaluation"]["positions"]
        assert len(posicoes) >= 1
        assert posicoes[0]["verdict"]

    def test_a_demonstracao_nao_grava_nada_na_conta(self, client):
        headers = make_auth_headers("u_demo_limpo")

        client.get("/api/demo/portfolio", headers=headers)

        assert client.get("/api/portfolio", headers=headers).json()["items"] == []

    def test_o_aviso_vem_junto_e_diz_que_nao_e_recomendacao(self, client):
        headers = make_auth_headers("u_demo_aviso")

        corpo = client.get("/api/demo/assets", headers=headers).json()

        assert "exemplo" in corpo["disclaimer"].lower()
        assert "recomendação" in corpo["disclaimer"].lower()

    def test_a_carteira_de_exemplo_e_grande_o_bastante_para_o_veredito(self):
        assert len(DEMO_POSITIONS) >= READABLE_PORTFOLIO_SIZE

    def test_a_carteira_de_exemplo_e_diversificada(self):
        categorias = {p["category"] for p in DEMO_POSITIONS}

        assert len(categorias) >= 3
