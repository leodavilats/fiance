from __future__ import annotations

import pytest

from app.core.config import get_settings
from app.entitlement import Feature, Plan, meter, plans
from app.services import subscription_service
from tests.conftest import make_auth_headers

ROTAS_PREMIUM = [
    ("get", "/api/strategy", None),
    ("post", "/api/quick-invest", {"cash_available": 1000}),
    ("post", "/api/projection/passive-income", {"monthly_contribution": 500}),
    ("get", "/api/income-compare", None),
]


def _chamar(client, metodo, url, corpo, headers):
    if metodo == "get":
        return client.get(url, headers=headers)
    return client.post(url, json=corpo or {}, headers=headers)


@pytest.fixture()
def regua_ligada(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "entitlements_enabled", True, raising=False)
    return settings


def free_de_verdade(client, user_id: str) -> dict:
    headers = make_auth_headers(user_id)
    client.post(
        "/api/portfolio/position",
        json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
        headers=headers,
    )
    subscription_service.cancel(user_id, reason="fim do trial")
    return headers


class TestFlagDesligada:
    @pytest.mark.parametrize(("metodo", "url", "corpo"), ROTAS_PREMIUM)
    def test_nenhuma_rota_cobra_com_a_regua_desligada(self, client, metodo, url, corpo):
        headers = make_auth_headers("u_rota_off")

        resposta = _chamar(client, metodo, url, corpo, headers)

        assert resposta.status_code != 402


class TestRotasPremium:
    @pytest.mark.parametrize(("metodo", "url", "corpo"), ROTAS_PREMIUM)
    def test_free_leva_402_nas_rotas_premium(self, client, regua_ligada, metodo, url, corpo):
        headers = free_de_verdade(client, "u_rota_free")

        resposta = _chamar(client, metodo, url, corpo, headers)

        assert resposta.status_code == 402

    def test_o_corpo_do_402_diz_o_que_falta(self, client, regua_ligada):
        headers = free_de_verdade(client, "u_rota_corpo")

        corpo = client.get("/api/strategy", headers=headers).json()["detail"]

        assert corpo["feature"] == "strategy"
        assert corpo["required_plan"] == "premium"
        assert corpo["plan"] == "free"
        assert corpo["reason"]

    @pytest.mark.parametrize(("metodo", "url", "corpo"), ROTAS_PREMIUM)
    def test_premium_passa(self, client, regua_ligada, metodo, url, corpo):
        headers = make_auth_headers("u_rota_premium")
        subscription_service.grant("u_rota_premium", "premium", 1990)

        resposta = _chamar(client, metodo, url, corpo, headers)

        assert resposta.status_code != 402

    def test_importar_operacoes_e_premium(self, client, regua_ligada):
        headers = free_de_verdade(client, "u_rota_import")

        bloqueado = client.post(
            "/api/transactions/import",
            json={"content": "PETR4 100 30,00"},
            headers=headers,
        )
        assert bloqueado.status_code == 402

        assert client.get("/api/transactions", headers=headers).status_code == 200


class TestPaginaDeAtivo:
    def test_o_teto_bloqueia_depois_de_consumido(self, client, regua_ligada):
        headers = free_de_verdade(client, "u_ativo_teto")
        limite = plans.limit_for(Feature.ASSET_PAGE, Plan.FREE)

        for _ in range(limite):
            assert client.get("/api/asset/VALE3", headers=headers).status_code == 200

        bloqueado = client.get("/api/asset/VALE3", headers=headers)

        assert bloqueado.status_code == 402
        assert bloqueado.json()["detail"]["limit_reached"] is True

    def test_ativo_da_propria_carteira_nunca_conta(self, client, regua_ligada):
        headers = make_auth_headers("u_ativo_carteira")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        for _ in range(20):
            assert client.get("/api/asset/PETR4", headers=headers).status_code == 200

        assert meter.used("u_ativo_carteira", Feature.ASSET_PAGE) == 0

    def test_ativo_fora_da_carteira_conta(self, client, regua_ligada):
        headers = make_auth_headers("u_ativo_fora")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        client.get("/api/asset/VALE3", headers=headers)

        assert meter.used("u_ativo_fora", Feature.ASSET_PAGE) == 1

    def test_a_pagina_publica_nao_consome_cota(self, client, regua_ligada):
        make_auth_headers("u_ativo_publico")

        for _ in range(20):
            assert client.get("/api/public/asset/PETR4").status_code == 200

        assert meter.used("u_ativo_publico", Feature.ASSET_PAGE) == 0


class TestNadaProibidoFoiCercado:
    def test_a_carteira_nunca_e_bloqueada(self, client, regua_ligada):
        headers = make_auth_headers("u_livre_carteira")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        assert client.get("/api/portfolio", headers=headers).status_code == 200

    def test_exportacao_e_exclusao_nunca_ficam_atras_de_plano(self, client, regua_ligada):
        headers = make_auth_headers("u_livre_export")

        assert client.get("/api/account/export", headers=headers).status_code == 200
        assert client.get("/api/account/deletion-policy", headers=headers).status_code == 200

    def test_o_resumo_da_carteira_continua_livre(self, client, regua_ligada):
        headers = make_auth_headers("u_livre_resumo")

        assert client.get("/api/dashboard", headers=headers).status_code != 402

    def test_proventos_recebidos_continuam_livres(self, client, regua_ligada):
        headers = make_auth_headers("u_livre_proventos")

        assert client.get("/api/dividends/received", headers=headers).status_code == 200


class TestTelemetriaDaCerca:
    def test_bater_no_teto_deixa_registro(self, client, regua_ligada):
        from app.storage import event_store

        headers = free_de_verdade(client, "u_cerca_evento")
        client.get("/api/strategy", headers=headers)

        assert event_store.has_event("u_cerca_evento", "paywall_viewed")

    def test_o_evento_diz_qual_feature_e_de_onde(self, client, regua_ligada):
        from app.storage import event_store

        headers = make_auth_headers("u_cerca_origem")
        client.get("/api/strategy", headers=headers)

        origens = event_store.counts_by_prop("paywall_viewed", "feature")

        assert origens.get("strategy", 0) >= 1


class TestNadaEBloqueadoAntesDeComecar:
    def test_conta_sem_carteira_nao_ve_gate(self, client, regua_ligada):
        headers = make_auth_headers("u_antes_de_comecar")

        assert client.get("/api/strategy", headers=headers).status_code != 402

    def test_a_primeira_posicao_e_o_que_liga_a_cerca(self, client, regua_ligada):
        headers = make_auth_headers("u_liga_a_cerca")
        antes = client.get("/api/strategy", headers=headers).status_code

        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )
        subscription_service.cancel("u_liga_a_cerca", reason="fim do trial")
        depois = client.get("/api/strategy", headers=headers).status_code

        assert (antes, depois) == (200, 402)

    def test_sem_carteira_nem_evento_de_paywall_e_gravado(self, client, regua_ligada):
        from app.storage import event_store

        headers = make_auth_headers("u_antes_sem_evento")
        client.get("/api/strategy", headers=headers)

        assert not event_store.has_event("u_antes_sem_evento", "paywall_viewed")
