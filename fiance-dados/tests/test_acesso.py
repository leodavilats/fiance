from __future__ import annotations

from datetime import date

import sqlalchemy as sa

from dadosapi import acesso
from tests.conftest import TOKEN, criar_conta

ADMIN = {"X-Admin-Token": TOKEN}


def test_sem_chave_ou_com_chave_errada_nao_entra(cliente):
    assert cliente.get("/v1/ativos").status_code == 401
    assert cliente.get("/v1/ativos", headers={"Authorization": "Bearer fd_xpto"}).status_code == 401
    assert cliente.get("/saude").status_code == 200
    assert cliente.get("/v1").status_code == 200, "o índice e a documentação são públicos"


def test_a_chave_vale_por_cabecalho_e_traz_o_limite(cliente, chave):
    resposta = cliente.get("/v1/ativos", headers=chave)
    alternativa = cliente.get("/v1/ativos", headers={"X-API-Key": chave["Authorization"][7:]})

    assert resposta.status_code == 200 and alternativa.status_code == 200
    assert resposta.headers["X-Limite-Dia"] == "20000"
    assert int(resposta.headers["X-Restante-Dia"]) == 19999
    assert "CVM (ODbL)" in resposta.headers["X-Fontes"], "a atribuição vai em toda resposta"


def test_a_base_guarda_so_o_hash(cliente, bancos):
    criada = criar_conta(cliente)

    with bancos.acesso.connect() as conn:
        guardado = conn.execute(sa.text("SELECT prefixo, hash FROM acesso.chave")).one()

    texto = criada["chave"]["chave"]
    assert guardado.hash == acesso.hash_da_chave(texto) and texto not in guardado.hash
    assert guardado.prefixo == texto[: acesso.TAMANHO_DO_PREFIXO]


def test_limite_do_dia(cliente, bancos, chave):
    with bancos.acesso.begin() as conn:
        conn.execute(
            sa.text("UPDATE acesso.plano SET limite_por_dia = 2 WHERE codigo = 'convidado'")
        )

    respostas = [cliente.get("/v1/ativos", headers=chave).status_code for _ in range(3)]

    assert respostas == [200, 200, 429]


def test_limite_por_minuto_reabre_no_minuto_seguinte():
    agora = [120.0]
    limite = acesso.LimitePorMinuto(relogio=lambda: agora[0])

    assert [limite.registrar(1, 2) for _ in range(2)] == [None, None]
    assert limite.registrar(1, 2) is not None, "a terceira no mesmo minuto espera"
    assert limite.registrar(2, 2) is None, "cada chave conta a sua"
    agora[0] = 181.0
    assert limite.registrar(1, 2) is None


def test_chave_revogada_e_conta_desativada_param_de_entrar(cliente, chave):
    extra = cliente.post("/v1/conta/chaves", json={"nome": "notebook"}, headers=chave)
    assert extra.status_code == 201
    segunda = {"Authorization": f"Bearer {extra.json()['dados']['chave']}"}

    revogada = cliente.delete(f"/v1/conta/chaves/{extra.json()['dados']['prefixo']}", headers=chave)
    assert revogada.status_code == 204
    assert cliente.get("/v1/ativos", headers=segunda).status_code == 401

    conta_id = cliente.get("/v1/conta", headers=chave).json()["dados"]["id"]
    cliente.patch(
        f"/admin/contas/{conta_id}", json={"ativa": False}, headers={"X-Admin-Token": TOKEN}
    )
    assert cliente.get("/v1/ativos", headers=chave).status_code == 401


def test_plano_limita_quantas_chaves_ativas(cliente, chave):
    respostas = [
        cliente.post("/v1/conta/chaves", json={"nome": f"c{i}"}, headers=chave).status_code
        for i in range(3)
    ]

    assert respostas == [201, 201, 409], "o convidado tem 3 chaves ativas"


def test_administracao_exige_o_token_e_nao_aparece_na_documentacao(cliente):
    assert cliente.get("/admin/contas").status_code == 401
    assert cliente.get("/admin/contas", headers={"X-Admin-Token": "errado"}).status_code == 401
    assert cliente.get("/admin/contas", headers={"X-Admin-Token": TOKEN}).status_code == 200
    assert not [r for r in cliente.get("/openapi.json").json()["paths"] if r.startswith("/admin")]


def test_email_repetido_e_plano_desconhecido_sao_recusados(cliente):
    criar_conta(cliente)
    cabecalho = {"X-Admin-Token": TOKEN}

    repetido = cliente.post(
        "/admin/contas", json={"email": "EU@teste.com", "nome": "x"}, headers=cabecalho
    )
    sem_plano = cliente.post(
        "/admin/contas", json={"email": "b@t.com", "nome": "x", "plano": "ouro"}, headers=cabecalho
    )

    assert repetido.status_code == 409 and sem_plano.status_code == 422


def test_portal_e_console_sao_paginas_sem_segredo(cliente):
    portal = cliente.get("/")
    console = cliente.get("/console")

    assert portal.status_code == 200 and "fiance dados" in portal.text
    assert console.status_code == 200 and "noindex" in console.text
    assert TOKEN not in console.text, "o token é digitado na tela, nunca entregue nela"


def test_dez_tentativas_erradas_bloqueiam_ate_o_token_certo(cliente):
    errado = {"X-Admin-Token": "errado"}
    respostas = [cliente.get("/admin/contas", headers=errado).status_code for _ in range(10)]

    assert respostas == [401] * 10
    assert cliente.get("/admin/contas", headers={"X-Admin-Token": TOKEN}).status_code == 429, (
        "a rota de administração fica no endereço público: chute não pode ser infinito"
    )


def test_uso_por_dia(cliente, chave):
    cliente.get("/v1/ativos", headers=chave)
    cliente.get("/v1/ativos", headers=chave)

    uso = cliente.get("/admin/uso", headers={"X-Admin-Token": TOKEN}).json()

    assert uso[-1]["requisicoes"] == 2 and uso[-1]["contas"] == 1


def test_situacao_da_conta_segue_a_regra_do_402():
    hoje = date(2026, 10, 14)

    assert acesso.situacao_da_conta(False, True, date(2099, 1, 1), hoje) == "desativada"
    assert acesso.situacao_da_conta(True, False, None, hoje) == "ativa"
    assert acesso.situacao_da_conta(True, True, None, hoje) == "sem_pagamento"
    assert acesso.situacao_da_conta(True, True, date(2026, 10, 12), hoje) == "em_tolerancia"
    assert acesso.situacao_da_conta(True, True, date(2026, 10, 10), hoje) == "sem_pagamento", (
        "passados os três dias de tolerância, a chave responde 402"
    )
    assert acesso.situacao_da_conta(True, True, date(2026, 10, 20), hoje) == "a_vencer"
    assert acesso.situacao_da_conta(True, True, date(2026, 12, 1), hoje) == "ativa"


def test_lista_de_contas_traz_situacao_limite_e_uso(cliente, chave):
    cliente.get("/v1/ativos", headers=chave)
    criar_conta(cliente, plano="pro", email="pago@teste.com")

    contas = {c["email"]: c for c in cliente.get("/admin/contas", headers=ADMIN).json()}

    convidado, pago = contas["eu@teste.com"], contas["pago@teste.com"]
    assert (convidado["situacao"], convidado["plano_pago"]) == ("ativa", False)
    assert convidado["requisicoes_hoje"] == convidado["maior_chave_hoje"] == 1
    assert convidado["requisicoes_30_dias"] == 1 and convidado["limite_por_dia"] == 20_000
    assert convidado["ultimo_uso_em"] is not None
    assert (pago["situacao"], pago["chaves_ativas"]) == ("sem_pagamento", 1)


def test_administracao_edita_nome_e_observacao_e_limpa_o_pago_ate(cliente):
    criada = criar_conta(cliente, plano="pro", email="edita@teste.com")
    rota = f"/admin/contas/{criada['conta']['id']}"

    cliente.patch(
        rota, json={"pago_ate": "2099-01-01", "observacao": " contrato 12 "}, headers=ADMIN
    )
    so_nome = cliente.patch(rota, json={"nome": "Novo nome"}, headers=ADMIN).json()
    limpa = cliente.patch(rota, json={"pago_ate": None, "observacao": ""}, headers=ADMIN).json()

    assert (so_nome["nome"], so_nome["pago_ate"], so_nome["observacao"]) == (
        "Novo nome",
        "2099-01-01",
        "contrato 12",
    ), "campo não enviado fica como estava"
    assert (limpa["pago_ate"], limpa["observacao"]) == (None, None), (
        "nulo enviado de propósito limpa o campo"
    )


def test_conta_paga_criada_com_pago_ate_ja_entra(cliente):
    resposta = cliente.post(
        "/admin/contas",
        json={
            "email": "contrato@teste.com",
            "nome": "C",
            "plano": "quant",
            "pago_ate": "2099-01-01",
        },
        headers=ADMIN,
    )
    chave = {"Authorization": f"Bearer {resposta.json()['chave']['chave']}"}

    assert cliente.get("/v1/ativos", headers=chave).status_code == 200


def test_administracao_revoga_chave_de_uma_conta(cliente, chave):
    conta = cliente.get("/admin/contas", headers=ADMIN).json()[0]
    prefixo = cliente.get(f"/admin/contas/{conta['id']}", headers=ADMIN).json()["chaves"][0][
        "prefixo"
    ]

    revogada = cliente.delete(f"/admin/contas/{conta['id']}/chaves/{prefixo}", headers=ADMIN)
    de_novo = cliente.delete(f"/admin/contas/{conta['id']}/chaves/{prefixo}", headers=ADMIN)

    assert revogada.status_code == 204 and de_novo.status_code == 404
    assert cliente.get("/v1/ativos", headers=chave).status_code == 401
    assert cliente.delete(f"/admin/contas/{conta['id']}/chaves/{prefixo}").status_code == 401


def test_uso_por_dia_filtra_por_conta(cliente, chave):
    cliente.get("/v1/ativos", headers=chave)
    outra = criar_conta(cliente, email="outra@teste.com")
    conta = cliente.get("/admin/contas", headers=ADMIN).json()[0]["id"]

    so_dela = cliente.get(f"/admin/uso?conta_id={conta}", headers=ADMIN).json()
    da_outra = cliente.get(f"/admin/uso?conta_id={outra['conta']['id']}", headers=ADMIN).json()

    assert so_dela[-1]["requisicoes"] == 1 and da_outra == []
