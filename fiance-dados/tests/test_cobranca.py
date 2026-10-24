from __future__ import annotations

from datetime import date

import httpx
import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from dadosapi import app, cobranca
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
        "pay_velho": {"id": "pay_velho", "status": "CONFIRMED", "subscription": "sub_velha", "dueDate": "2026-10-15"},
    }  # fmt: skip

    criadas = []

    def responder(pedido: httpx.Request) -> httpx.Response:
        pedidos.append(pedido)
        rota = pedido.url.path
        if pedido.method == "DELETE" and rota.startswith("/v3/subscriptions/"):
            return httpx.Response(200, json={"deleted": True, "id": rota.rsplit("/", 1)[1]})
        if rota == "/v3/customers":
            return httpx.Response(200, json={"id": "cus_1"})
        if rota == "/v3/subscriptions":
            criadas.append(f"sub_{len(criadas) + 1}")
            return httpx.Response(200, json={"id": criadas[-1]})
        if rota.startswith("/v3/subscriptions/") and rota.endswith("/payments"):
            numero = rota.split("/")[3].removeprefix("sub_")
            return httpx.Response(
                200,
                json={
                    "data": [
                        {"status": "RECEIVED", "invoiceUrl": "https://asaas/pago"},
                        {"status": "PENDING", "invoiceUrl": f"https://asaas/pagar/{numero}"},
                    ]
                },
            )
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


def test_assinar_de_novo_cancela_a_anterior_e_ignora_o_pagamento_dela(
    com_cobranca, chave, bancos, pedidos
):
    conta_id = com_cobranca.get("/v1/conta", headers=chave).json()["dados"]["id"]
    with bancos.acesso.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO acesso.assinatura (conta_id, plano, ciclo, asaas_cliente, "
                "asaas_assinatura, situacao) VALUES (:c, 'essencial', 'mensal', 'cus', "
                "'sub_velha', 'ativa')"
            ),
            {"c": conta_id},
        )

    nova = com_cobranca.post(
        "/v1/conta/assinatura",
        json={"plano": "pro", "nome": "Fulano", "cpf_cnpj": "12345678909"},
        headers=chave,
    )
    pagamento_velho = com_cobranca.post(
        "/cobranca/asaas",
        json=_evento("evt_velho", "PAYMENT_CONFIRMED", "pay_velho"),
        headers={"asaas-access-token": WEBHOOK},
    )

    assert nova.status_code == 201
    assert ("DELETE", "/v3/subscriptions/sub_velha") in [(p.method, p.url.path) for p in pedidos]
    assert pagamento_velho.json()["resultado"].startswith("ignorado: assinatura substituída"), (
        "a cobrança atrasada do Essencial não pode devolver ao Essencial quem assinou o Pro"
    )
    assert com_cobranca.get("/v1/conta", headers=chave).json()["dados"]["plano"] == "convidado"


def _cadastro(email: str = "novo@teste.com") -> dict:
    return {"plano": "pro", "nome": "Nova", "email": email, "cpf_cnpj": "12345678909"}


def test_assinar_sem_conta_devolve_a_chave_que_so_vale_depois_do_pagamento(com_cobranca):
    resposta = com_cobranca.post("/v1/assinatura", json=_cadastro())
    dados = resposta.json()["dados"]
    chave = {"Authorization": f"Bearer {dados['chave']}"}

    antes = com_cobranca.get("/v1/ativos", headers=chave).status_code
    com_cobranca.post(
        "/cobranca/asaas",
        json=_evento("evt_novo", "PAYMENT_CONFIRMED", "pay_1"),
        headers={"asaas-access-token": WEBHOOK},
    )
    depois = com_cobranca.get("/v1/ativos", headers=chave).status_code

    assert resposta.status_code == 201 and dados["pagar_em"] == "https://asaas/pagar/1"
    assert (antes, depois) == (402, 200), "a chave sai na hora, e o pagamento é o que a libera"


def test_assinar_sem_conta_nao_toma_o_email_de_quem_ja_tem_conta(com_cobranca, chave, pedidos):
    resposta = com_cobranca.post("/v1/assinatura", json=_cadastro("EU@teste.com"))

    assert resposta.status_code == 409 and "Minha conta" in resposta.json()["erro"]
    assert pedidos == [], "nada vai ao Asaas quando o e-mail já é de uma conta"


def test_cadastro_que_nunca_pagou_e_retomado_e_a_chave_antiga_cai(com_cobranca, bancos):
    primeira = com_cobranca.post("/v1/assinatura", json=_cadastro()).json()["dados"]
    aguardando = com_cobranca.post("/v1/assinatura", json=_cadastro())
    with bancos.acesso.begin() as conn:
        conn.execute(sa.text("UPDATE acesso.assinatura SET criada_em = now() - interval '8 days'"))

    segunda = com_cobranca.post("/v1/assinatura", json=_cadastro())
    antiga = {"Authorization": f"Bearer {primeira['chave']}"}

    assert aguardando.status_code == 409, (
        "assinatura recente aguardando pagamento segura o e-mail: outro não a derruba"
    )
    assert segunda.status_code == 201, "cadastro que nunca pagou não prende o e-mail para sempre"
    assert com_cobranca.get("/v1/ativos", headers=antiga).status_code == 401


def test_cadastro_tem_teto_por_endereco(com_cobranca):
    respostas = [
        com_cobranca.post("/v1/assinatura", json=_cadastro(f"n{i}@teste.com")).status_code
        for i in range(app.CADASTROS_POR_HORA + 1)
    ]

    assert respostas == [201] * app.CADASTROS_POR_HORA + [429]


def test_assinar_sem_conta_com_a_cobranca_desligada(cliente):
    assert cliente.post("/v1/assinatura", json=_cadastro()).status_code == 503


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


def _pagar(cliente, evento: str = "evt_pago") -> None:
    cliente.post(
        "/cobranca/asaas",
        json=_evento(evento, "PAYMENT_CONFIRMED", "pay_1"),
        headers={"asaas-access-token": WEBHOOK},
    )


def test_quem_ainda_nao_pagou_entra_em_minha_conta_e_ve_o_link(com_cobranca):
    feito = com_cobranca.post("/v1/assinatura", json=_cadastro()).json()["dados"]
    chave = {"Authorization": f"Bearer {feito['chave']}"}

    conta = com_cobranca.get("/v1/conta", headers=chave)
    dados_de_mercado = com_cobranca.get("/v1/ativos", headers=chave)

    assert conta.status_code == 200, "a conta sem pagamento entra; só os dados respondem 402"
    assert dados_de_mercado.status_code == 402
    dados = conta.json()["dados"]
    assert dados["situacao"] == "aguardando_pagamento"
    assert dados["assinatura"]["situacao"] == "aguardando"
    assert dados["assinatura"]["pagar_em"] == "https://asaas/pagar/1", (
        "o link é a cobrança em aberto, não a já paga"
    )
    assert "asaas_assinatura" not in dados["assinatura"]
    assert dados["cadastro_de_cobranca"] is True
    assert dados["requisicoes_hoje"] == 0, "abrir Minha conta não gasta a cota do dia"


def test_assinante_vencido_renova_pela_conta_sem_repetir_o_cpf(com_cobranca, pedidos):
    feito = com_cobranca.post("/v1/assinatura", json=_cadastro()).json()["dados"]
    chave = {"Authorization": f"Bearer {feito['chave']}"}
    _pagar(com_cobranca)
    conta_id = com_cobranca.get("/v1/conta", headers=chave).json()["dados"]["id"]
    com_cobranca.patch(
        f"/admin/contas/{conta_id}",
        json={"pago_ate": "2020-01-01"},
        headers={"X-Admin-Token": TOKEN},
    )

    vencida = com_cobranca.get("/v1/conta", headers=chave).json()["dados"]
    renovada = com_cobranca.post("/v1/conta/assinatura", json={"plano": "essencial"}, headers=chave)

    assert vencida["situacao"] == "sem_pagamento"
    assert renovada.status_code == 201, renovada.text
    clientes = [p for p in pedidos if p.url.path == "/v3/customers"]
    assert len(clientes) == 1, "a renovação usa o cliente do Asaas que já existe"


def test_assinar_sem_cadastro_de_cobranca_pede_nome_e_documento(com_cobranca, chave, pedidos):
    resposta = com_cobranca.post("/v1/conta/assinatura", json={"plano": "pro"}, headers=chave)

    assert resposta.status_code == 422
    assert pedidos == []


def test_convidado_que_assina_ve_o_link_ate_pagar(com_cobranca, chave):
    com_cobranca.post(
        "/v1/conta/assinatura",
        json={"plano": "pro", "nome": "Fulano", "cpf_cnpj": "12345678909"},
        headers=chave,
    )

    dados = com_cobranca.get("/v1/conta", headers=chave).json()["dados"]

    assert dados["situacao"] == "ativa", "o convidado segue com acesso enquanto não paga"
    assert dados["assinatura"]["pagar_em"] == "https://asaas/pagar/1"


def test_asaas_fora_do_ar_nao_vira_ausencia_de_cobranca(com_cobranca, monkeypatch):
    feito = com_cobranca.post("/v1/assinatura", json=_cadastro()).json()["dados"]

    def fora(*_):
        raise httpx.ConnectError("sem rede")

    monkeypatch.setattr(cobranca, "link_em_aberto", fora)
    conta = com_cobranca.get("/v1/conta", headers={"Authorization": f"Bearer {feito['chave']}"})

    assinatura = conta.json()["dados"]["assinatura"]
    assert conta.status_code == 200
    assert assinatura["pagar_em"] is None and assinatura["pagar_em_indisponivel"] is True


def test_console_separa_quem_aguarda_pagamento_de_quem_venceu(com_cobranca):
    com_cobranca.post("/v1/assinatura", json=_cadastro())

    contas = com_cobranca.get("/admin/contas", headers={"X-Admin-Token": TOKEN}).json()

    assert [c["situacao"] for c in contas] == ["aguardando_pagamento"]
