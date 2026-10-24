from __future__ import annotations

import json
import threading
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
PAGADOR = {"nome": "Fulano", "cpf_cnpj": "123.456.789-09", "cep": "01310-100", "numero": "1000"}


@pytest.fixture
def pedidos() -> list[httpx.Request]:
    return []


@pytest.fixture
def pagamentos() -> dict[str, dict]:
    return {
        "pay_1": {"id": "pay_1", "status": "CONFIRMED", "subscription": "sub_1", "dueDate": "2026-10-15"},
        "pay_x": {"id": "pay_x", "status": "CONFIRMED", "subscription": "sub_de_outro", "dueDate": "2026-10-15"},
        "pay_pendente": {"id": "pay_pendente", "status": "PENDING", "subscription": "sub_1", "dueDate": "2026-10-15"},
        "pay_velho": {"id": "pay_velho", "status": "CONFIRMED", "subscription": "sub_velha", "dueDate": "2026-10-15"},
    }  # fmt: skip


@pytest.fixture
def recusas() -> dict[tuple[str, str], int]:
    return {}


@pytest.fixture
def asaas(pedidos, pagamentos, recusas):
    criadas = []

    def responder(pedido: httpx.Request) -> httpx.Response:
        pedidos.append(pedido)
        rota = pedido.url.path
        if (pedido.method, rota) in recusas:
            erro = {"errors": [{"description": "recusado no teste"}]}
            return httpx.Response(recusas[(pedido.method, rota)], json=erro)
        if pedido.method == "DELETE" and rota.startswith("/v3/subscriptions/"):
            return httpx.Response(200, json={"deleted": True, "id": rota.rsplit("/", 1)[1]})
        if rota == "/v3/customers":
            return httpx.Response(200, json={"id": "cus_1"})
        if rota == "/v3/subscriptions":
            criadas.append(f"sub_{len(criadas) + 1}")
            return httpx.Response(200, json={"id": criadas[-1]})
        if rota.startswith("/v3/subscriptions/") and rota.endswith("/payments"):
            assinatura = rota.split("/")[3]
            numero = assinatura.removeprefix("sub_")
            status = pedido.url.params.get("status")
            cobrancas = [
                {"status": "PENDING", "invoiceUrl": f"https://asaas/pagar/{numero}"},
                *(p for p in pagamentos.values() if p["subscription"] == assinatura),
            ]
            return httpx.Response(
                200, json={"data": [c for c in cobrancas if status in (None, c["status"])]}
            )
        if rota.startswith("/v3/payments/") and rota.endswith("/refund"):
            pagamento = pagamentos[rota.split("/")[3]]
            pagamento["status"] = "REFUND_IN_PROGRESS"
            return httpx.Response(200, json=pagamento)
        if rota.startswith("/v3/payments/"):
            pagamento = pagamentos.get(rota.rsplit("/", 1)[1])
            return httpx.Response(404) if pagamento is None else httpx.Response(200, json=pagamento)
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
        json={"plano": "pro", **PAGADOR},
        headers=chave,
    )

    assert assinatura.status_code == 503
    assert cliente.post("/cobranca/asaas", json={}).status_code == 503


def test_assinar_cria_cliente_e_assinatura_e_devolve_o_link(com_cobranca, chave, pedidos, bancos):
    resposta = com_cobranca.post(
        "/v1/conta/assinatura",
        json={"plano": "pro", "ciclo": "anual", **PAGADOR},
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
        json={"plano": "pro", **PAGADOR},
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
        json={"plano": "pro", **PAGADOR},
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
        json={"plano": "pro", **PAGADOR},
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
        json={"plano": "pro", **PAGADOR},
        headers=chave,
    )
    pagamento_velho = com_cobranca.post(
        "/cobranca/asaas",
        json=_evento("evt_velho", "PAYMENT_CONFIRMED", "pay_velho"),
        headers={"asaas-access-token": WEBHOOK},
    )

    assert nova.status_code == 201
    chamadas = [(p.method, p.url.path) for p in pedidos]
    assert ("DELETE", "/v3/subscriptions/sub_velha") in chamadas
    assert chamadas.index(("POST", "/v3/subscriptions")) < chamadas.index(
        ("DELETE", "/v3/subscriptions/sub_velha")
    ), "a antiga só cai depois que a nova existe"
    assert pagamento_velho.json()["resultado"].startswith("estornado:"), (
        "a cobrança atrasada do Essencial não pode devolver ao Essencial quem assinou o Pro"
    )
    assert ("POST", "/v3/payments/pay_velho/refund") in [(p.method, p.url.path) for p in pedidos]
    assert com_cobranca.get("/v1/conta", headers=chave).json()["dados"]["plano"] == "convidado"


def _cadastro(email: str = "novo@teste.com") -> dict:
    return {"plano": "pro", **PAGADOR, "nome": "Nova", "email": email}


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
        json={"plano": "pro", **PAGADOR},
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


def _assinar_e_pagar(cliente, pagamentos) -> dict:
    feito = cliente.post("/v1/assinatura", json=_cadastro()).json()["dados"]
    _pagar(cliente, "evt_pay_1")
    return {"Authorization": f"Bearer {feito['chave']}"}


def _webhook(cliente, evento: str, tipo: str, pagamento: str) -> str:
    return cliente.post(
        "/cobranca/asaas",
        json=_evento(evento, tipo, pagamento),
        headers={"asaas-access-token": WEBHOOK},
    ).json()["resultado"]


def _assinatura_antiga(cliente, chave, bancos) -> None:
    conta_id = cliente.get("/v1/conta", headers=chave).json()["dados"]["id"]
    with bancos.acesso.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO acesso.assinatura (conta_id, plano, ciclo, asaas_cliente, "
                "asaas_assinatura, situacao) VALUES (:c, 'essencial', 'mensal', 'cus_1', "
                "'sub_velha', 'ativa')"
            ),
            {"c": conta_id},
        )


def test_cpf_e_cnpj_valem_pelo_digito_e_o_cnpj_aceita_letras():
    assert cobranca.documento_valido("123.456.789-09") == "12345678909"
    assert cobranca.documento_valido("11.222.333/0001-81") == "11222333000181"
    assert cobranca.documento_valido("12.abc.345/01de-35") == "12ABC34501DE35", (
        "o CNPJ alfanumérico vale desde julho de 2026"
    )
    for invalido in ("123.456.789-00", "111.111.111-11", "11222333000182", "1234567890", ""):
        assert cobranca.documento_valido(invalido) is None, invalido


def test_documento_invalido_nao_cria_conta_nem_vai_ao_asaas(com_cobranca, pedidos, bancos):
    resposta = com_cobranca.post("/v1/assinatura", json={**_cadastro(), "cpf_cnpj": "12345678900"})

    assert resposta.status_code == 422
    assert "CPF ou CNPJ inválido" in resposta.json()["erro"]
    assert pedidos == []
    with bancos.acesso.connect() as conn:
        contas = conn.execute(sa.text("SELECT count(*) FROM acesso.conta")).scalar_one()
    assert contas == 0, "a recusa do Asaas chegava depois da conta e da chave já gravadas"


def test_cadastro_de_cobranca_exige_cep_e_numero(com_cobranca, chave, pedidos):
    sem_endereco = {"plano": "pro", "nome": "Fulano", "cpf_cnpj": "12345678909"}
    cep_errado = {"plano": "pro", **PAGADOR, "cep": "0131-100"}

    faltando = com_cobranca.post("/v1/conta/assinatura", json=sem_endereco, headers=chave)
    errado = com_cobranca.post("/v1/conta/assinatura", json=cep_errado, headers=chave)

    assert faltando.status_code == 422 and "CEP e número" in faltando.json()["erro"]
    assert errado.status_code == 422 and "CEP" in errado.json()["erro"]
    assert pedidos == []


def test_cliente_e_assinatura_levam_endereco_telefone_e_a_conta(com_cobranca, pedidos):
    com_cobranca.post("/v1/assinatura", json={**_cadastro(), "telefone": "+55 (11) 98765-4321"})

    contas = com_cobranca.get("/admin/contas", headers={"X-Admin-Token": TOKEN}).json()
    cliente = json.loads(next(p for p in pedidos if p.url.path == "/v3/customers").content)
    assinatura = json.loads(next(p for p in pedidos if p.url.path == "/v3/subscriptions").content)
    assert cliente["cpfCnpj"] == "12345678909", "o Asaas recebe o documento sem máscara"
    assert (cliente["postalCode"], cliente["addressNumber"]) == ("01310100", "1000")
    assert cliente["mobilePhone"] == "11987654321"
    assert cliente["externalReference"] == assinatura["externalReference"] == str(contas[0]["id"])


def test_troca_que_o_asaas_recusa_nao_derruba_a_assinatura_antiga(
    com_cobranca, chave, bancos, pedidos, recusas
):
    _assinatura_antiga(com_cobranca, chave, bancos)
    recusas[("POST", "/v3/subscriptions")] = 400

    resposta = com_cobranca.post("/v1/conta/assinatura", json={"plano": "pro"}, headers=chave)

    assert resposta.status_code == 502
    assert not [p for p in pedidos if p.method == "DELETE"], (
        "cancelar antes de criar deixava o assinante sem assinatura nenhuma"
    )
    with bancos.acesso.connect() as conn:
        situacao = conn.execute(sa.text("SELECT situacao FROM acesso.assinatura")).scalar_one()
    assert situacao == "ativa"


def test_cancelamento_que_falha_fica_para_a_conferencia(com_cobranca, chave, bancos, recusas):
    _assinatura_antiga(com_cobranca, chave, bancos)
    recusas[("DELETE", "/v3/subscriptions/sub_velha")] = 500

    nova = com_cobranca.post("/v1/conta/assinatura", json={"plano": "pro"}, headers=chave)
    recusas.clear()
    relatorio = com_cobranca.post(
        "/admin/cobranca/conferir", headers={"X-Admin-Token": TOKEN}
    ).json()

    assert nova.status_code == 201, "a nova já existe: a falha em cancelar a antiga não a desfaz"
    assert "assinatura sub_velha cancelada no Asaas" in relatorio["aplicados"]
    with bancos.acesso.connect() as conn:
        pendente = conn.execute(
            sa.text(
                "SELECT cancelamento_pendente FROM acesso.assinatura "
                "WHERE asaas_assinatura = 'sub_velha'"
            )
        ).scalar_one()
    assert pendente is False


def test_estorno_tira_o_acesso_que_o_pagamento_deu(com_cobranca, pagamentos):
    chave = _assinar_e_pagar(com_cobranca, pagamentos)
    assert com_cobranca.get("/v1/ativos", headers=chave).status_code == 200

    pagamentos["pay_1"]["status"] = "REFUNDED"
    resultado = _webhook(com_cobranca, "evt_estorno", "PAYMENT_REFUNDED", "pay_1")

    assert "pagamento desfeito (REFUNDED), pago até 2026-10-14" in resultado
    assert com_cobranca.get("/v1/ativos", headers=chave).status_code == 402


def test_chargeback_de_um_mes_volta_ao_mes_pago_antes(com_cobranca, pagamentos):
    chave = _assinar_e_pagar(com_cobranca, pagamentos)
    pagamentos["pay_2"] = {"id": "pay_2", "status": "RECEIVED", "subscription": "sub_1", "dueDate": "2026-11-15"}  # fmt: skip
    _webhook(com_cobranca, "evt_pay_2", "PAYMENT_RECEIVED", "pay_2")
    assert com_cobranca.get("/v1/conta", headers=chave).json()["dados"]["pago_ate"] == "2026-12-15"

    pagamentos["pay_2"]["status"] = "CHARGEBACK_REQUESTED"
    _webhook(com_cobranca, "evt_chargeback", "PAYMENT_CHARGEBACK_REQUESTED", "pay_2")

    assert com_cobranca.get("/v1/conta", headers=chave).json()["dados"]["pago_ate"] == "2026-11-15"


def test_estorno_de_mes_antigo_nao_corta_o_mes_pago_depois(com_cobranca, pagamentos):
    chave = _assinar_e_pagar(com_cobranca, pagamentos)
    pagamentos["pay_2"] = {"id": "pay_2", "status": "RECEIVED", "subscription": "sub_1", "dueDate": "2026-11-15"}  # fmt: skip
    _webhook(com_cobranca, "evt_pay_2", "PAYMENT_RECEIVED", "pay_2")

    pagamentos["pay_1"]["status"] = "REFUNDED"
    resultado = _webhook(com_cobranca, "evt_estorno", "PAYMENT_REFUNDED", "pay_1")

    assert resultado.endswith("o acesso não dependia dele")
    assert com_cobranca.get("/v1/conta", headers=chave).json()["dados"]["pago_ate"] == "2026-12-15"


def test_cobranca_removida_que_nao_e_nossa_nao_mexe_na_conta(com_cobranca, pagamentos):
    chave = _assinar_e_pagar(com_cobranca, pagamentos)

    resultado = _webhook(com_cobranca, "evt_removida", "PAYMENT_DELETED", "pay_sumiu")

    assert resultado == "ignorado: assinatura que não é nossa"
    assert com_cobranca.get("/v1/ativos", headers=chave).status_code == 200


def test_conferencia_aplica_o_pagamento_que_o_webhook_perdeu(com_cobranca):
    feito = com_cobranca.post("/v1/assinatura", json=_cadastro()).json()["dados"]
    chave = {"Authorization": f"Bearer {feito['chave']}"}
    conta_id = com_cobranca.get("/v1/conta", headers=chave).json()["dados"]["id"]
    assert com_cobranca.get("/v1/ativos", headers=chave).status_code == 402

    primeira = com_cobranca.post("/admin/cobranca/conferir", headers={"X-Admin-Token": TOKEN})
    segunda = com_cobranca.post("/admin/cobranca/conferir", headers={"X-Admin-Token": TOKEN})

    assert primeira.json()["aplicados"] == [f"pagamento pay_1: conta {conta_id} no plano pro"]
    assert segunda.json()["aplicados"] == [], "a conferência aplica cada pagamento uma vez"
    assert com_cobranca.get("/v1/ativos", headers=chave).status_code == 200


def test_conferencia_acha_o_estorno_que_o_webhook_perdeu(com_cobranca, pagamentos):
    chave = _assinar_e_pagar(com_cobranca, pagamentos)
    pagamentos["pay_1"]["status"] = "REFUNDED"

    com_cobranca.post("/admin/cobranca/conferir", headers={"X-Admin-Token": TOKEN})

    assert com_cobranca.get("/v1/ativos", headers=chave).status_code == 402


def test_evento_parado_e_estorno_a_mao_aparecem_no_console(com_cobranca, bancos):
    with bancos.acesso.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO acesso.evento_de_cobranca (id, tipo, recebido_em, resultado) VALUES "
                "('evt_parado', 'PAYMENT_RECEIVED', now() - interval '2 hours', NULL), "
                "('evt_chegando', 'PAYMENT_RECEIVED', now(), NULL), "
                "('evt_mao', 'PAYMENT_RECEIVED', now(), 'ignorado: x; estornar à mão (y)'), "
                "('evt_ok', 'PAYMENT_RECEIVED', now() - interval '2 hours', 'conta 1 no plano pro')"
            )
        )

    painel = com_cobranca.get("/admin/cobranca", headers={"X-Admin-Token": TOKEN}).json()

    assert painel["ligada"] is True
    assert {p["id"] for p in painel["pendencias"]} == {"evt_parado", "evt_mao"}, (
        "evento recém-chegado ainda está sendo aplicado"
    )


def test_o_link_e_o_da_cobranca_vencida_antes_da_pendente(com_cobranca, pagamentos, chave):
    com_cobranca.post("/v1/conta/assinatura", json={"plano": "pro", **PAGADOR}, headers=chave)
    pagamentos["pay_atrasado"] = {"id": "pay_atrasado", "status": "OVERDUE", "subscription": "sub_1", "dueDate": "2026-09-15", "invoiceUrl": "https://asaas/atrasada"}  # fmt: skip

    dados = com_cobranca.get("/v1/conta", headers=chave).json()["dados"]

    assert dados["assinatura"]["pagar_em"] == "https://asaas/atrasada"


def test_estorno_negado_da_substituida_vai_para_a_mao(com_cobranca, chave, bancos, pagamentos):
    _assinatura_antiga(com_cobranca, chave, bancos)
    com_cobranca.post("/v1/conta/assinatura", json={"plano": "pro"}, headers=chave)
    _webhook(com_cobranca, "evt_velho", "PAYMENT_CONFIRMED", "pay_velho")

    pagamentos["pay_velho"]["status"] = "RECEIVED"
    negado = _webhook(com_cobranca, "evt_negado", "PAYMENT_REFUND_DENIED", "pay_velho")

    assert "estornar à mão" in negado, "boleto pode ter o estorno negado, e o dinheiro fica"
    painel = com_cobranca.get("/admin/cobranca", headers={"X-Admin-Token": TOKEN}).json()
    assert [p["id"] for p in painel["pendencias"]] == ["evt_negado"]


def test_pagamento_antigo_nao_muda_o_plano_de_quem_ja_esta_pago_adiante(com_cobranca, pagamentos):
    chave = _assinar_e_pagar(com_cobranca, pagamentos)
    conta_id = com_cobranca.get("/v1/conta", headers=chave).json()["dados"]["id"]
    com_cobranca.patch(
        f"/admin/contas/{conta_id}",
        json={"plano": "essencial", "pago_ate": "2027-06-30"},
        headers={"X-Admin-Token": TOKEN},
    )
    pagamentos["pay_2"] = {"id": "pay_2", "status": "RECEIVED", "subscription": "sub_1", "dueDate": "2026-11-15"}  # fmt: skip

    _webhook(com_cobranca, "evt_pay_2", "PAYMENT_RECEIVED", "pay_2")

    conta = com_cobranca.get("/v1/conta", headers=chave).json()["dados"]
    assert (conta["plano"], conta["pago_ate"]) == ("essencial", "2027-06-30"), (
        "a primeira conferência reaplica pagamentos antigos: o ajuste à mão não pode voltar"
    )


def test_conta_desativada_sai_de_vez_e_a_assinatura_cai_no_asaas(
    com_cobranca, pagamentos, pedidos, bancos
):
    chave = _assinar_e_pagar(com_cobranca, pagamentos)
    conta_id = com_cobranca.get("/v1/conta", headers=chave).json()["dados"]["id"]
    admin = {"X-Admin-Token": TOKEN}

    ativa = com_cobranca.delete(f"/admin/contas/{conta_id}", headers=admin)
    com_cobranca.patch(f"/admin/contas/{conta_id}", json={"ativa": False}, headers=admin)
    removida = com_cobranca.delete(f"/admin/contas/{conta_id}", headers=admin)

    assert ativa.status_code == 409, "só sai de vez a conta já desativada"
    assert removida.status_code == 204
    assert ("DELETE", "/v3/subscriptions/sub_1") in [(p.method, p.url.path) for p in pedidos], (
        "apagar só aqui deixaria o Asaas cobrando quem não tem mais conta"
    )
    assert com_cobranca.get(f"/admin/contas/{conta_id}", headers=admin).status_code == 404
    with bancos.acesso.connect() as conn:
        restos = conn.execute(
            sa.text(
                "SELECT (SELECT count(*) FROM acesso.chave) + (SELECT count(*) FROM "
                "acesso.assinatura) + (SELECT count(*) FROM acesso.pagamento)"
            )
        ).scalar_one()
    assert restos == 0
    assert com_cobranca.post("/v1/assinatura", json=_cadastro()).status_code == 201, (
        "o e-mail fica livre"
    )


def test_remover_conta_que_o_asaas_nao_cancela_nao_apaga_nada(com_cobranca, pagamentos, recusas):
    chave = _assinar_e_pagar(com_cobranca, pagamentos)
    conta_id = com_cobranca.get("/v1/conta", headers=chave).json()["dados"]["id"]
    admin = {"X-Admin-Token": TOKEN}
    com_cobranca.patch(f"/admin/contas/{conta_id}", json={"ativa": False}, headers=admin)
    recusas[("DELETE", "/v3/subscriptions/sub_1")] = 500

    resposta = com_cobranca.delete(f"/admin/contas/{conta_id}", headers=admin)

    assert resposta.status_code == 502
    assert com_cobranca.get(f"/admin/contas/{conta_id}", headers=admin).status_code == 200


def test_convidado_desativado_sai_com_a_cobranca_desligada(cliente):
    criada = criar_conta(cliente, email="sai@teste.com")
    chave = {"Authorization": f"Bearer {criada['chave']['chave']}"}
    cliente.get("/v1/ativos", headers=chave)
    admin = {"X-Admin-Token": TOKEN}
    conta_id = criada["conta"]["id"]

    cliente.patch(f"/admin/contas/{conta_id}", json={"ativa": False}, headers=admin)
    removida = cliente.delete(f"/admin/contas/{conta_id}", headers=admin)

    assert removida.status_code == 204, "a chave usada deixa uso gravado, que sai junto"
    assert cliente.delete(f"/admin/contas/{conta_id}", headers=admin).status_code == 404


def test_a_conferencia_roda_sozinha_ate_parar(monkeypatch):
    monkeypatch.setattr(app, "PRIMEIRA_CONFERENCIA", 0)
    monkeypatch.setattr(app, "CONFERENCIA_A_CADA", 0)
    parar, rodadas = threading.Event(), []

    def conferir() -> dict:
        rodadas.append(1)
        if len(rodadas) == 3:
            parar.set()
        return {}

    app._conferir_sempre(conferir, parar)

    assert len(rodadas) == 3
