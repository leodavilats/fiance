from __future__ import annotations

from app.storage import interest_store


class TestQuemDeixaOEmail:
    def test_o_email_entra_e_a_rota_e_publica(self, client):
        resp = client.post("/api/public/interest", json={"email": "alguem@exemplo.com"})

        assert resp.status_code == 200, resp.text
        assert resp.json()["registered"] is True

    def test_cadastrar_de_novo_nao_e_erro(self, client):
        client.post("/api/public/interest", json={"email": "repetido@exemplo.com"})
        resp = client.post("/api/public/interest", json={"email": "repetido@exemplo.com"})

        assert resp.status_code == 200
        assert resp.json()["registered"] is False, (
            "quem nao lembra se ja cadastrou tenta de novo; isso nao pode parecer falha"
        )

    def test_maiuscula_e_espaco_nao_criam_duas_pessoas(self, client):
        client.post("/api/public/interest", json={"email": "Igual@Exemplo.com"})
        resp = client.post("/api/public/interest", json={"email": "  igual@exemplo.com  "})

        assert resp.json()["registered"] is False

    def test_email_invalido_e_recusado(self, client):
        resp = client.post("/api/public/interest", json={"email": "sem-arroba"})

        assert resp.status_code == 422


class TestOQueNaoSaiDaqui:
    def test_a_lista_nao_e_legivel_por_rota(self, client):
        client.post("/api/public/interest", json={"email": "sigilo@exemplo.com"})

        for caminho in ["/api/public/interest", "/api/interest", "/api/public/interests"]:
            assert client.get(caminho).status_code in (404, 405), (
                f"{caminho} nao pode devolver a lista de quem se cadastrou"
            )

    def test_a_tabela_e_global_e_nao_de_ninguem(self):
        from app.storage.account_store import GLOBAL_TABLES

        assert "interest_signups" in GLOBAL_TABLES, (
            "sem dono, ela nao entra em exportacao nem exclusao de conta — quem deixou o e-mail "
            "ainda nao tem conta"
        )

    def test_o_store_conta_sem_expor_quem(self):
        antes = interest_store.count()
        interest_store.register("contagem@exemplo.com")

        assert interest_store.count() == antes + 1
