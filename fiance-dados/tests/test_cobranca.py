from __future__ import annotations

from datetime import date

import httpx
import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from dadosapi import cobranca
from dadosapi.app import criar
from dadosapi.config import Configuracao
from tests.conftest import TOKEN, criar_conta

WEBHOOK = "w" * 40


@pytest.fixture
def pedidos() -> list[httpx.Request]:
    return []


@pytest.fixture
def asaas(pedidos):
    pagamentos = {
        "pay_1": {"id": "pay_1", "status": "CONFIRMED", "subscription": "sub_1", "dueDate": "2026-10-15"},
        "pay_x": {"id": "pay_x", "status": "CONFIRMED", "subscription": "sub_de_outro", "dueDate": "2026-10-15"},
        "pay_pendente": {"id": "pay_pendente", "status": "PENDING", "subscription": "sub_1", "dueDate": "2026-10-15"},
    }  # fmt: skip

    def responder(pedido: httpx.Request) -> httpx.Response:
        pedidos.append(pedido)
        rota = pedido.url.path
        if rota == "/v3/customers":
            return httpx.Response(200, json={"id": "cus_1"})
        if rota == "/v3/subscriptions":
            return httpx.Response(200, json={"id": "sub_1"})
        if rota == "/v3/subscriptions/sub_1/payments":
            return httpx.Response(200, json={"data": [{"invoiceUrl": "https://asaas/pagar/1"}]})
        if rota.startswith("/v3/payments/"):
            return httpx.Response(200, json=pagamentos[rota.rsplit("/", 1)[1]])
        return httpx.Response(404)

    cliente = httpx.Client(
        base_url="https://asaas.teste/v3",
        transport=httpx.MockTransport(responder),
        headers={"access_token": "chave"},
    )
    return cobranca.Asaas(cliente, WEBHOOK)


@pytest.fixture
def com_cobranca(bancos, url, asaas):
    config = Configuracao(url, TOKEN, cobranca_ativa=True)
    return TestClient(criar(config, bancos, asaas))


def _evento(evento_id: str, tipo: str, pagamento: str) -> dict:
    return {"id": evento_id, "event": tipo, "payment": {"id": pagamento, "subscription": "sub_1"}}


def test_cobranca_desligada_nao_cria_assinatura_nem_aceita_webhook(cliente, chave):
    assinatura = cliente.post(
        "/v1/conta/assinatura",
        json={"plano": "pro", "nome": "Fulano", "cpf_cnpj": "12345678909"},
        headers=chave,
    )

    assert assinatura.status_code == 503
    assert cliente.post("/cobranca/asaas", json={}).status_code == 503


def test_assinar_cria_cliente_e_assinatura_e_devolve_o_link(com_cobranca, chave, pedidos, bancos):
    resposta = com_cobranca.post(
        "/v1/conta/assinatura",
        json={"plano": "pro", "ciclo": "anual", "nome": "Fulano", "cpf_cnpj": "12345678909"},
        headers=chave,
    )

    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["dados"] == {"assinatura": "sub_1", "pagar_em": "https://asaas/pagar/1"}
    pedido = next(p for p in pedidos if p.url.path == "/v3/subscriptions")
    assert b'"value":1490.0' in pedido.content and b'"cycle":"YEARLY"' in pedido.content
    with bancos.acesso.connect() as conn:
        guardada = conn.execute(sa.text("SELECT plano, ciclo FROM acesso.assinatura")).one()
    assert tuple(guardada) == ("pro", "anual")


def test_pagamento_confirmado_libera_o_plano_ate_o_fim_do_ciclo(com_cobranca, chave, bancos):
    com_cobranca.post(
        "/v1/conta/assinatura",
        json={"plano": "pro", "nome": "Fulano", "cpf_cnpj": "12345678909"},
        headers=chave,
    )
    cabecalho = {"asaas-access-token": WEBHOOK}

    primeira = com_cobranca.post(
        "/cobranca/asaas", json=_evento("evt_1", "PAYMENT_CONFIRMED", "pay_1"), headers=cabecalho
    )
    repetida = com_cobranca.post("/cobranca/asaas", json=_evento("evt_1", "PAYMENT_CONFIRMED", "pay_1"), headers=cabecalho)  # fmt: skip

    assert primeira.json()["resultado"].endswith("no plano pro")
    assert repetida.json()["resultado"] == "repetido", (
        "o Asaas entrega o mesmo evento mais de uma vez"
    )
    conta = com_cobranca.get("/v1/conta", headers=chave).json()["dados"]
    assert (conta["plano"], conta["pago_ate"]) == ("pro", "2026-11-15")


def test_o_titular_nao_sai_do_corpo_do_webhook(com_cobranca, chave, bancos):
    cabecalho = {"asaas-access-token": WEBHOOK}

    alheio = com_cobranca.post("/cobranca/asaas", json=_evento("evt_2", "PAYMENT_CONFIRMED", "pay_x"), headers=cabecalho)  # fmt: skip
    pendente = com_cobranca.post("/cobranca/asaas", json=_evento("evt_3", "PAYMENT_CONFIRMED", "pay_pendente"), headers=cabecalho)  # fmt: skip

    assert alheio.json()["resultado"] == "ignorado: assinatura que não é nossa"
    assert pendente.json()["resultado"] == "ignorado: o Asaas diz PENDING", (
        "o corpo diz confirmado; quem decide é a consulta ao Asaas"
    )


def test_evento_que_falhou_no_meio_e_aplicado_na_reentrega(com_cobranca, chave, bancos):
    com_cobranca.post(
        "/v1/conta/assinatura",
        json={"plano": "pro", "nome": "Fulano", "cpf_cnpj": "12345678909"},
        headers=chave,
    )
    with bancos.acesso.begin() as conn:
        conn.execute(
            sa.text("INSERT INTO acesso.evento_de_cobranca (id, tipo) VALUES ('evt_9', 'x')")
        )

    reentrega = com_cobranca.post(
        "/cobranca/asaas",
        json=_evento("evt_9", "PAYMENT_CONFIRMED", "pay_1"),
        headers={"asaas-access-token": WEBHOOK},
    )

    assert reentrega.json()["resultado"].endswith("no plano pro"), (
        "evento gravado sem resultado caiu antes de aplicar: tratá-lo como repetido perde o pagamento"
    )


def test_assinatura_tem_teto_por_dia(com_cobranca, chave, bancos, pedidos):
    conta_id = com_cobranca.get("/v1/conta", headers=chave).json()["dados"]["id"]
    with bancos.acesso.begin() as conn:
        for i in range(cobranca.ASSINATURAS_POR_DIA):
            conn.execute(
                sa.text(
                    "INSERT INTO acesso.assinatura (conta_id, plano, ciclo, asaas_cliente, "
                    "asaas_assinatura) VALUES (:c, 'pro', 'mensal', 'cus', :a)"
                ),
                {"c": conta_id, "a": f"sub_antiga_{i}"},
            )

    resposta = com_cobranca.post(
        "/v1/conta/assinatura",
        json={"plano": "pro", "nome": "Fulano", "cpf_cnpj": "12345678909"},
        headers=chave,
    )

    assert resposta.status_code == 429 and pedidos == [], (
        "cada assinatura cria cliente e cobrança no Asaas"
    )


def test_recusa_do_asaas_volta_so_com_a_descricao():
    resposta = httpx.Response(400, json={"errors": [{"code": "x", "description": "CPF inválido"}]})

    assert cobranca._motivo(resposta) == "CPF inválido"
    assert cobranca._motivo(httpx.Response(500, text="<html>pilha</html>")) == "status 500"


def test_webhook_sem_o_token_combinado_e_recusado(com_cobranca):
    errado = com_cobranca.post(
        "/cobranca/asaas",
        json={"id": "x", "event": "PAYMENT_CONFIRMED"},
        headers={"asaas-access-token": "x"},
    )

    assert errado.status_code == 401


def test_ciclo_soma_mes_e_ano_respeitando_o_fim_do_mes():
    assert cobranca._somar_ciclo(date(2026, 1, 31), "mensal") == date(2026, 2, 28)
    assert cobranca._somar_ciclo(date(2026, 12, 15), "mensal") == date(2027, 1, 15)
    assert cobranca._somar_ciclo(date(2024, 2, 29), "anual") == date(2025, 2, 28)


def test_admin_cria_conta_paga_e_marca_pagamento(cliente):
    criada = criar_conta(cliente, plano="essencial", email="manual@teste.com")
    chave = {"Authorization": f"Bearer {criada['chave']['chave']}"}
    assert cliente.get("/v1/ativos", headers=chave).status_code == 402

    cliente.patch(
        f"/admin/contas/{criada['conta']['id']}",
        json={"pago_ate": "2099-01-01"},
        headers={"X-Admin-Token": TOKEN},
    )

    assert cliente.get("/v1/ativos", headers=chave).status_code == 200, (
        "contrato e pagamento por fora entram pela administração"
    )
