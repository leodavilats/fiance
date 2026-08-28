"""Jornadas completas: da primeira posição à cobrança, ao churn e à saída.

Os testes de módulo provam que cada peça funciona. Estes provam que a corrente
fecha — e é na emenda que o dinheiro se perde. Uma posição salva tem que
disparar o marco, que dispara o trial, que muda o direito, que abre o gate, que
leva ao checkout, que gera o webhook, que concede, que expira, que degrada. Cada
seta dessa é código de um módulo que não conhece o outro.

Aqui não há dublê de camada: as chamadas passam pelo app de verdade, com HTTP,
autenticação e banco. O que não passa por aqui é o navegador — a interface
Angular não é exercitada, e isso está registrado como aberto em
`docs/KNOWN_ISSUES.md` em vez de sugerido pelo nome do arquivo.
"""

from __future__ import annotations

import json
import time

import pytest

from app.entitlement import Plan, resolve
from app.payments import FakeProvider, billing
from app.services import referral_service, subscription_service
from tests.conftest import make_auth_headers


@pytest.fixture()
def regua_ligada(monkeypatch):
    """A cerca de plano ligada. Em produção ela entra desligada."""
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "entitlements_enabled", True, raising=False)


@pytest.fixture()
def gateway():
    falso = FakeProvider(secret="segredo-de-jornada")
    billing.set_provider(falso)
    yield falso
    billing.set_provider(None)


def comprar(client, gateway, user_id: str, plano: str = "premium_monthly", evento: str = "e"):
    """O caminho inteiro da compra: checkout, e depois o webhook que concede."""
    client.post(
        "/api/billing/checkout", json={"plan_code": plano}, headers=make_auth_headers(user_id)
    )
    corpo = json.dumps(
        {
            "id": f"evt_{evento}_{user_id}",
            "type": "checkout.completed",
            "user_id": user_id,
            "plan_code": plano,
            "price_cents": 1990,
        }
    ).encode()
    return client.post(
        "/api/billing/webhook", content=corpo, headers={"X-Signature": gateway.sign(corpo)}
    )


def salvar_posicao(client, user_id: str, ticker: str = "PETR4"):
    return client.post(
        "/api/portfolio/position",
        json={"ticker": ticker, "quantity": 100, "avg_price": 30.0},
        headers=make_auth_headers(user_id),
    )


class TestDoCadastroAoTrial:
    """A corrente que começa numa escrita de carteira e termina num direito."""

    def test_a_primeira_posicao_dispara_o_trial_e_o_trial_da_premium(self, client, regua_ligada):
        uid = "j_trial"
        assert resolve(uid).plan is Plan.FREE

        salvar_posicao(client, uid)

        direitos = resolve(uid)
        assert direitos.plan is Plan.PREMIUM
        assert direitos.in_trial is True

    def test_conta_sem_carteira_nao_gasta_trial(self, client, regua_ligada):
        """Trial que expira antes de a pessoa ter o que analisar é trial
        desperdiçado — ela nunca chega a ver o que estaria comprando."""
        uid = "j_sem_carteira"
        client.get("/api/entitlements", headers=make_auth_headers(uid))

        assert subscription_service.get(uid)["trial_started_at"] is None

    def test_passado_o_trial_degrada_sozinho(self, client, regua_ligada):
        uid = "j_trial_vence"
        salvar_posicao(client, uid)

        depois = time.time() + 15 * 86400
        assert resolve(uid, now=depois).plan is Plan.FREE

    def test_degradar_nao_apaga_a_carteira(self, client, regua_ligada):
        """Cancelar Premium não é cancelar conta. Sumir com a carteira no fim
        do trial produz pedido de exclusão, não upgrade."""
        uid = "j_trial_carteira"
        salvar_posicao(client, uid)
        subscription_service.cancel(uid, reason="teste")

        resposta = client.get("/api/portfolio", headers=make_auth_headers(uid))

        assert resposta.status_code == 200
        assert any(p["ticker"] == "PETR4" for p in resposta.json()["items"])


class TestDoLimiteAoPagamento:
    """Encostar no teto, ver o gate, pagar, e o teto sumir."""

    def test_free_encosta_no_teto_e_o_402_traz_o_que_a_ui_precisa(self, client, regua_ligada):
        uid = "j_teto"
        headers = make_auth_headers(uid)

        # A régua dá 5 páginas de ativo por mês fora da carteira.
        respostas = [client.get(f"/api/asset/ATIVO{i}", headers=headers) for i in range(7)]
        bloqueadas = [r for r in respostas if r.status_code == 402]

        assert bloqueadas, "o teto de páginas por mês nunca foi atingido"
        corpo = bloqueadas[0].json()["detail"]
        assert corpo["feature"] and corpo["plan"] and corpo["reason"]

    def test_a_compra_derruba_o_teto(self, client, gateway, regua_ligada):
        uid = "j_compra"
        headers = make_auth_headers(uid)
        for i in range(7):
            client.get(f"/api/asset/ANTES{i}", headers=headers)

        comprar(client, gateway, uid, evento="teto")

        assert resolve(uid).plan is Plan.PREMIUM
        assert client.get("/api/asset/DEPOIS1", headers=headers).status_code != 402

    def test_o_checkout_sozinho_nao_libera_nada(self, client, gateway, regua_ligada):
        """Conceder no checkout daria Premium a quem abandonou o pagamento."""
        uid = "j_abandonou"
        client.post(
            "/api/billing/checkout",
            json={"plan_code": "premium_monthly"},
            headers=make_auth_headers(uid),
        )

        assert resolve(uid).plan is Plan.FREE


class TestDoChurnAoDado:
    """Cancelar, degradar, exportar e sair — sem nada disso ficar atrás do
    plano."""

    def test_cancelar_degrada_mas_nao_apaga(self, client, gateway, regua_ligada):
        uid = "j_churn"
        salvar_posicao(client, uid)
        comprar(client, gateway, uid, evento="churn")
        assert resolve(uid).plan is Plan.PREMIUM

        subscription_service.cancel(uid, reason="user_request")

        assert resolve(uid).plan is Plan.FREE
        assert client.get("/api/portfolio", headers=make_auth_headers(uid)).status_code == 200

    def test_exportar_funciona_no_plano_free(self, client, regua_ligada):
        """Cobrar pela exportação é confiscar o dado de quem parou de pagar."""
        uid = "j_export"
        salvar_posicao(client, uid)
        subscription_service.cancel(uid, reason="teste")

        resposta = client.get("/api/account/export", headers=make_auth_headers(uid))

        assert resposta.status_code == 200
        assert resposta.json()["data"]["positions"]

    def test_excluir_funciona_no_plano_free_e_leva_tudo(self, client, regua_ligada):
        uid = "j_delete"
        salvar_posicao(client, uid)
        subscription_service.cancel(uid, reason="teste")

        resposta = client.request(
            "DELETE",
            "/api/account",
            json={"confirm": "EXCLUIR"},
            headers=make_auth_headers(uid),
        )

        assert resposta.status_code == 200
        assert resposta.json()["deleted"] is True

    def test_a_sessao_morre_com_a_conta(self, client, regua_ligada):
        """Token vivo depois da exclusão ressuscitaria a conta na primeira
        escrita."""
        uid = "j_delete_sessao"
        headers = make_auth_headers(uid)
        salvar_posicao(client, uid)
        client.request("DELETE", "/api/account", json={"confirm": "EXCLUIR"}, headers=headers)

        assert client.get("/api/portfolio", headers=headers).status_code == 401


class TestCercasQueNuncaPodemExistir:
    """As proibições do plano, escritas como teste em vez de como intenção.

    Elas não têm representação na régua — então o que se testa é o
    comportamento, que é o que o usuário sente.
    """

    def test_a_propria_carteira_nunca_e_bloqueada(self, client, regua_ligada):
        """Limitar o número de ativos da carteira seria cobrar por guardar o
        que já é da pessoa."""
        uid = "j_carteira_livre"
        for ticker in ("PETR4", "VALE3", "ITUB4", "BBAS3", "WEGE3", "MGLU3", "ABEV3"):
            assert salvar_posicao(client, uid, ticker).status_code in (200, 201)

        assert client.get("/api/portfolio", headers=make_auth_headers(uid)).status_code == 200

    def test_ativo_da_propria_carteira_nao_consome_cota(self, client, regua_ligada):
        """Olhar o que já é seu não pode gastar as páginas do mês."""
        uid = "j_cota_propria"
        headers = make_auth_headers(uid)
        salvar_posicao(client, uid, "PETR4")

        for _ in range(10):
            resposta = client.get("/api/asset/PETR4", headers=headers)
            assert resposta.status_code != 402

    def test_a_avaliacao_da_carteira_nunca_e_cercada(self, client, regua_ligada):
        """Borrar saldo, P&L ou composição é pegar o que já é da pessoa e
        escondê-lo até ela pagar."""
        uid = "j_resumo"
        salvar_posicao(client, uid)
        subscription_service.cancel(uid, reason="teste")

        resposta = client.post("/api/portfolio/evaluate", json={}, headers=make_auth_headers(uid))

        assert resposta.status_code != 402

    def test_a_rota_publica_nao_pede_plano_nem_conta(self, client):
        """É o canal de aquisição: robô de busca não faz login."""
        resposta = client.get("/api/public/asset/PETR4")

        assert resposta.status_code != 402
        assert resposta.status_code != 401


class TestJornadaDaIndicacao:
    def test_do_link_ao_premium_dos_dois_lados(self, client, regua_ligada):
        indicador, indicado = "j_ind_dono", "j_ind_novo"
        codigo = referral_service.code_for(indicador)
        referral_service.attribute(indicado, codigo)
        assert resolve(indicador).plan is Plan.FREE

        salvar_posicao(client, indicado)

        assert resolve(indicador).plan is Plan.PREMIUM
        assert referral_service.status(indicador)["qualified"] == 1

    def test_o_credito_tem_prazo(self, client, regua_ligada):
        """Crédito é empréstimo de Premium, não upgrade permanente."""
        indicador, indicado = "j_ind_prazo", "j_ind_prazo_novo"
        referral_service.attribute(indicado, referral_service.code_for(indicador))
        salvar_posicao(client, indicado)

        muito_depois = time.time() + 400 * 86400
        assert resolve(indicador, now=muito_depois).plan is Plan.FREE


class TestOQueNinguemVeQuandoQuebra:
    def test_webhook_perdido_aparece_na_reconciliacao(self, client, gateway):
        """Silencioso dos dois lados: o gateway acha que entregou, o produto
        nunca soube, e a pessoa só descobre quando tenta usar."""
        gateway.granted["j_perdido"] = {"status": "active"}

        divergencias = {d["user_id"]: d for d in billing.reconcile()["divergences"]}

        assert divergencias["j_perdido"]["reason"] == "pago_sem_direito"

    def test_o_reenvio_do_webhook_nao_concede_duas_vezes(self, client, gateway, regua_ligada):
        uid = "j_reenvio"
        primeira = comprar(client, gateway, uid, evento="dup").json()
        segunda = comprar(client, gateway, uid, evento="dup").json()

        assert primeira["applied"] is True
        assert segunda["applied"] is False
