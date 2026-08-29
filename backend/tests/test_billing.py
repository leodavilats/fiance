from __future__ import annotations

import json

import pytest

from app.entitlement import Plan, resolve
from app.payments import FakeProvider, billing
from app.services import subscription_service
from tests.conftest import make_auth_headers


@pytest.fixture()
def gateway(monkeypatch):
    falso = FakeProvider(secret="segredo-de-teste")
    billing.set_provider(falso)
    yield falso
    billing.set_provider(None)


@pytest.fixture()
def regua_ligada(monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "entitlements_enabled", True, raising=False)


def _enviar(client, gateway, payload: dict, assinatura: str | None = None):
    corpo = json.dumps(payload).encode()
    return client.post(
        "/api/billing/webhook",
        content=corpo,
        headers={"X-Signature": assinatura if assinatura is not None else gateway.sign(corpo)},
    )


class TestCatalogo:
    def test_o_catalogo_traz_o_equivalente_mensal(self, client):
        headers = make_auth_headers("u_bill_catalogo")

        ofertas = {
            o["code"]: o for o in client.get("/api/billing/plans", headers=headers).json()["offers"]
        }

        assert ofertas["premium_monthly"]["price_cents"] == 1990
        assert ofertas["premium_yearly"]["monthly_equivalent_cents"] == 1499
        assert ofertas["premium_founder"]["founder"] is True

    def test_a_oferta_de_fundador_declara_que_o_preco_nao_reajusta(self, client):
        headers = make_auth_headers("u_bill_fundador")

        ofertas = {
            o["code"]: o for o in client.get("/api/billing/plans", headers=headers).json()["offers"]
        }

        assert "não é reajustado" in ofertas["premium_founder"]["note"]


class TestCheckout:
    def test_checkout_cria_sessao_e_nao_concede_nada(self, client, gateway, regua_ligada):
        headers = make_auth_headers("u_bill_checkout")

        corpo = client.post(
            "/api/billing/checkout", json={"plan_code": "premium_monthly"}, headers=headers
        ).json()

        assert corpo["url"].startswith("https://")
        assert resolve("u_bill_checkout").plan is Plan.FREE

    def test_plano_inexistente_e_recusado_com_a_lista(self, client, gateway):
        headers = make_auth_headers("u_bill_plano_ruim")

        resposta = client.post(
            "/api/billing/checkout", json={"plan_code": "premium_vitalicio"}, headers=headers
        )

        assert resposta.status_code == 422
        assert "premium_monthly" in resposta.json()["detail"]

    def test_abrir_o_checkout_deixa_evento(self, client, gateway):
        from app.storage import event_store

        headers = make_auth_headers("u_bill_evento")
        client.post("/api/billing/checkout", json={"plan_code": "premium_yearly"}, headers=headers)

        assert event_store.has_event("u_bill_evento", "upgrade_started")


class TestAssinaturaDoWebhook:
    def test_assinatura_invalida_e_recusada(self, client, gateway):
        resposta = _enviar(
            client,
            gateway,
            {"id": "evt_forjado", "type": "checkout.completed", "user_id": "u_bill_forjado"},
            assinatura="0" * 64,
        )

        assert resposta.status_code == 401
        assert subscription_service.get("u_bill_forjado")["status"] == "none"

    def test_sem_assinatura_e_recusado(self, client, gateway):
        resposta = _enviar(client, gateway, {"id": "e", "type": "x", "user_id": "u"}, assinatura="")

        assert resposta.status_code == 401

    def test_corpo_alterado_invalida_a_assinatura(self, client, gateway):
        original = json.dumps(
            {"id": "evt_1", "type": "checkout.completed", "user_id": "u_a"}
        ).encode()
        assinatura = gateway.sign(original)

        adulterado = json.dumps(
            {"id": "evt_1", "type": "checkout.completed", "user_id": "u_atacante"}
        ).encode()

        resposta = client.post(
            "/api/billing/webhook", content=adulterado, headers={"X-Signature": assinatura}
        )

        assert resposta.status_code == 401

    def test_a_verificacao_e_em_tempo_constante(self):
        import inspect

        fonte = inspect.getsource(FakeProvider.verify)

        assert "compare_digest" in fonte


class TestWebhookIdempotente:
    def test_o_evento_concede_o_direito(self, client, gateway, regua_ligada):
        _enviar(
            client,
            gateway,
            {
                "id": "evt_grant",
                "type": "checkout.completed",
                "user_id": "u_bill_grant",
                "plan_code": "premium_monthly",
                "price_cents": 1990,
            },
        )

        assert resolve("u_bill_grant").plan is Plan.PREMIUM

    def test_o_reenvio_nao_concede_duas_vezes(self, client, gateway, regua_ligada):
        payload = {
            "id": "evt_repetido",
            "type": "checkout.completed",
            "user_id": "u_bill_repetido",
            "plan_code": "premium_monthly",
            "price_cents": 1990,
        }

        primeira = _enviar(client, gateway, payload).json()
        segunda = _enviar(client, gateway, payload).json()

        assert primeira["applied"] is True
        assert segunda["applied"] is False
        assert segunda["reason"] == "already_processed"

    def test_o_reenvio_responde_200_e_nao_erro(self, client, gateway):
        payload = {
            "id": "evt_200",
            "type": "checkout.completed",
            "user_id": "u_bill_200",
            "plan_code": "premium_monthly",
        }
        _enviar(client, gateway, payload)

        assert _enviar(client, gateway, payload).status_code == 200

    def test_evento_sem_usuario_e_recusado(self, client, gateway):
        resposta = _enviar(client, gateway, {"id": "evt_sem_dono", "type": "checkout.completed"})

        assert resposta.status_code == 400

    def test_evento_sem_id_e_recusado(self, client, gateway):
        resposta = _enviar(client, gateway, {"type": "checkout.completed", "user_id": "u"})

        assert resposta.status_code == 400

    def test_tipo_desconhecido_e_ignorado_sem_quebrar(self, client, gateway):
        corpo = _enviar(
            client, gateway, {"id": "evt_estranho", "type": "invoice.upcoming", "user_id": "u_x"}
        ).json()

        assert corpo["effect"] == "ignored"

    def test_cancelamento_degrada(self, client, gateway, regua_ligada):
        _enviar(
            client,
            gateway,
            {
                "id": "evt_c1",
                "type": "checkout.completed",
                "user_id": "u_bill_cancel",
                "plan_code": "premium_monthly",
                "price_cents": 1990,
            },
        )
        _enviar(
            client,
            gateway,
            {"id": "evt_c2", "type": "subscription.cancelled", "user_id": "u_bill_cancel"},
        )

        assert resolve("u_bill_cancel").plan is Plan.FREE


class TestPrecoDoEvento:
    def test_o_preco_gravado_vem_do_evento_e_nao_da_tabela(self, client, gateway):
        _enviar(
            client,
            gateway,
            {
                "id": "evt_preco",
                "type": "checkout.completed",
                "user_id": "u_bill_preco",
                "plan_code": "premium_monthly",
                "price_cents": 990,
            },
        )

        assert subscription_service.get("u_bill_preco")["price_cents"] == 990

    def test_fundador_entra_travado(self, client, gateway):
        _enviar(
            client,
            gateway,
            {
                "id": "evt_fund",
                "type": "checkout.completed",
                "user_id": "u_bill_fund",
                "plan_code": "premium_founder",
                "price_cents": 14990,
            },
        )

        assinatura = subscription_service.get("u_bill_fund")
        assert assinatura["locked"] is True
        assert assinatura["price_cents"] == 14990

    def test_mensal_nao_entra_travado(self, client, gateway):
        _enviar(
            client,
            gateway,
            {
                "id": "evt_mensal",
                "type": "checkout.completed",
                "user_id": "u_bill_mensal",
                "plan_code": "premium_monthly",
                "price_cents": 1990,
            },
        )

        assert subscription_service.get("u_bill_mensal")["locked"] is False


class TestReconciliacao:
    def test_sem_divergencia_quando_os_dois_lados_batem(self, client, gateway):
        gateway.granted["u_rec_ok"] = {"status": "active"}
        _enviar(
            client,
            gateway,
            {
                "id": "evt_rec_ok",
                "type": "checkout.completed",
                "user_id": "u_rec_ok",
                "plan_code": "premium_monthly",
                "price_cents": 1990,
            },
        )

        divergencias = [d for d in billing.reconcile()["divergences"] if d["user_id"] == "u_rec_ok"]

        assert divergencias == []

    def test_pagou_e_nao_recebeu_e_acusado(self, gateway):
        gateway.granted["u_rec_pagou"] = {"status": "active"}

        divergencias = {d["user_id"]: d for d in billing.reconcile()["divergences"]}

        assert divergencias["u_rec_pagou"]["reason"] == "pago_sem_direito"

    def test_direito_sem_pagamento_e_acusado(self, gateway):
        subscription_service.grant("u_rec_fantasma", "premium", 1990, provider="fake")

        divergencias = {d["user_id"]: d for d in billing.reconcile()["divergences"]}

        assert divergencias["u_rec_fantasma"]["reason"] == "direito_sem_pagamento"

    def test_a_reconciliacao_e_rota_de_operador(self, client, gateway):
        headers = make_auth_headers("u_rec_rota")

        assert client.get("/api/billing/reconciliation", headers=headers).status_code == 200


class TestCanalTrocavel:
    def test_o_direito_nao_depende_do_provedor(self, gateway, regua_ligada):
        subscription_service.grant("u_canal", "premium", 1990, provider="play")

        assert resolve("u_canal").plan is Plan.PREMIUM

    def test_trocar_o_provedor_nao_exige_reescrever_o_fluxo(self, gateway):
        outro = FakeProvider(name="outro", secret="x")
        billing.set_provider(outro)

        sessao = billing.start_checkout("u_troca", "premium_monthly")

        assert sessao["provider"] == "outro"
