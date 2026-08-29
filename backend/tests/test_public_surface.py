from __future__ import annotations

import pytest

from app.api import public
from app.core.config import get_settings
from tests.conftest import make_auth_headers


class TestSemAutenticacao:
    def test_a_pagina_de_ativo_responde_sem_token(self, client):
        resposta = client.get("/api/public/asset/PETR4")

        assert resposta.status_code == 200
        corpo = resposta.json()
        assert corpo["symbol"] == "PETR4"
        assert corpo["decision"]["verdict"]
        assert corpo["fair_price"]

    def test_o_universo_responde_sem_token(self, client):
        corpo = client.get("/api/public/universe").json()

        assert corpo["count"] > 0
        assert "PETR4" in corpo["tickers"]
        assert len(corpo["lastmod"]) == 10

    def test_ativo_inexistente_devolve_404_e_nao_500(self, client):
        assert client.get("/api/public/asset/NAOEXISTE99").status_code == 404

    def test_a_rota_autenticada_continua_exigindo_token(self, client):
        assert client.get("/api/asset/PETR4").status_code == 401


class TestImpessoalidade:
    def test_a_mesma_url_devolve_o_mesmo_conteudo_com_e_sem_sessao(self, client):
        anonimo = client.get("/api/public/asset/PETR4").json()

        headers = make_auth_headers("u_public_prefs")
        client.put(
            "/api/preferences",
            json={"desired_yield_stock": 0.20},
            headers=headers,
        )
        com_sessao = client.get("/api/public/asset/PETR4", headers=headers).json()

        assert com_sessao["fair_price"] == anonimo["fair_price"]

    def test_a_analise_personalizada_continua_reagindo_a_preferencia(self, client):
        headers = make_auth_headers("u_public_contrast")

        client.put("/api/preferences", json={"desired_yield_stock": 0.03}, headers=headers)
        baixo = client.get("/api/asset/PETR4", headers=headers).json()

        client.put("/api/preferences", json={"desired_yield_stock": 0.25}, headers=headers)
        alto = client.get("/api/asset/PETR4", headers=headers).json()

        assert baixo["fair_price"] != alto["fair_price"]


class TestTetoPorIp:
    @pytest.fixture()
    def teto_ligado(self, monkeypatch):
        settings = get_settings()
        monkeypatch.setattr(settings, "rate_limit_enabled", True, raising=False)
        monkeypatch.setattr(public, "PUBLIC_PER_MINUTE", 3)

    def test_sem_usuario_o_contador_e_por_endereco(self, client, teto_ligado):
        codigos = [client.get("/api/public/asset/PETR4").status_code for _ in range(5)]

        assert 429 in codigos
        assert codigos[0] == 200

    def test_a_resposta_bloqueada_diz_quando_voltar(self, client, teto_ligado):
        for _ in range(5):
            resposta = client.get("/api/public/asset/PETR4")
            if resposta.status_code == 429:
                assert resposta.headers["Retry-After"] == "60"
                return

        pytest.fail("o teto não foi atingido")
