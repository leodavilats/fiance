from __future__ import annotations

from datetime import date

import sqlalchemy as sa

from dadosapi import acesso, app
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


def test_trocar_de_chave_nao_renova_o_limite_do_dia(cliente, bancos, chave):
    with bancos.acesso.begin() as conn:
        conn.execute(
            sa.text("UPDATE acesso.plano SET limite_por_dia = 1 WHERE codigo = 'convidado'")
        )
    cliente.get("/v1/ativos", headers=chave)
    nova = cliente.post("/v1/conta/chaves", json={"nome": "outra"}, headers=chave).json()["dados"]
    cliente.delete(f"/v1/conta/chaves/{nova['prefixo']}", headers=chave)
    terceira = cliente.post("/v1/conta/chaves", json={"nome": "mais"}, headers=chave).json()
    outra = {"Authorization": f"Bearer {terceira['dados']['chave']}"}

    resposta = cliente.get("/v1/ativos", headers=outra)

    assert resposta.status_code == 429, (
        "a chave nova herda o uso da conta, inclusive o das chaves revogadas"
    )


def test_chaves_novas_tem_teto_por_dia(cliente, chave):
    respostas = []
    for i in range(app.CHAVES_NOVAS_POR_DIA):
        criada = cliente.post("/v1/conta/chaves", json={"nome": f"c{i}"}, headers=chave)
        respostas.append(criada.status_code)
        if criada.status_code == 201:
            cliente.delete(f"/v1/conta/chaves/{criada.json()['dados']['prefixo']}", headers=chave)

    assert respostas[-1] == 429 and set(respostas[:-1]) == {201}, (
        "a primeira chave da conta entra no teto: emitir e revogar não vira chave infinita"
    )


def test_limite_por_minuto_reabre_no_minuto_seguinte():
    agora = [120.0]
    limite = acesso.LimitePorMinuto(relogio=lambda: agora[0])

    assert [limite.registrar(1, 2) for _ in range(2)] == [None, None]
    assert limite.registrar(1, 2) is not None, "a terceira no mesmo minuto espera"
    assert limite.registrar(2, 2) is None, "cada conta conta a sua"
    agora[0] = 181.0
    assert limite.registrar(1, 2) is None


def test_chave_revogada_e_conta_desativada_param_de_entrar(cliente, chave):
    extra = cliente.post("/v1/conta/chaves", json={"nome": "notebook"}, headers=chave)
    assert extra.status_code == 201
    segunda = {"Authorization": f"Bearer {extra.json()['dados']['chave']}"}

    revogada = cliente.delete(f"/v1/conta/chaves/{extra.json()['dados']['prefixo']}", headers=chave)
    assert revogada.status_code == 204
    assert cliente.get("/v1/ativos", headers=segunda).status_code == 401
    assert cliente.get("/v1/conta", headers=segunda).status_code == 401

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


def test_x_forwarded_for_forjado_nao_escapa_do_bloqueio(cliente):
    for i in range(10):
        forjado = {"X-Admin-Token": "errado", "X-Forwarded-For": f"10.0.0.{i}, 203.0.113.9"}
        cliente.get("/admin/contas", headers=forjado)

    certo = {"X-Admin-Token": TOKEN, "X-Forwarded-For": "10.9.9.9, 203.0.113.9"}

    assert cliente.get("/admin/contas", headers=certo).status_code == 429, (
        "a origem é o endereço que o proxy acrescentou, à direita; o da esquerda o cliente escreve"
    )


def test_token_com_caractere_fora_do_ascii_e_recusado_sem_erro(cliente):
    resposta = cliente.get("/admin/contas", headers={"X-Admin-Token": "é".encode("latin-1")})

    assert resposta.status_code == 401


def test_conta_nao_ve_a_observacao_da_administracao(cliente, chave):
    conta_id = cliente.get("/v1/conta", headers=chave).json()["dados"]["id"]
    cliente.patch(f"/admin/contas/{conta_id}", json={"observacao": "nota interna"}, headers=ADMIN)
    cliente.get("/v1/ativos", headers=chave)

    propria = cliente.get("/v1/conta", headers=chave).json()["dados"]
    na_administracao = cliente.get(f"/admin/contas/{conta_id}", headers=ADMIN).json()

    assert "observacao" not in propria and na_administracao["observacao"] == "nota interna"
    assert propria["requisicoes_hoje"] == 1, "conta o uso dos dados; abrir a conta não gasta a cota"


def test_respostas_trazem_cabecalhos_de_seguranca(cliente):
    cabecalhos = cliente.get("/console").headers

    assert cabecalhos["Content-Security-Policy"] == "frame-ancestors 'none'"
    assert cabecalhos["X-Content-Type-Options"] == "nosniff"


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
    assert convidado["requisicoes_hoje"] == 1
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
            "plano": "pro",
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


SENHA = "uma senha longa"


def _com_senha(cliente, chave) -> dict:
    definida = cliente.put("/v1/conta/senha", json={"senha": SENHA}, headers=chave)
    assert definida.status_code == 200, definida.text
    return {"Authorization": f"Bearer {definida.json()['dados']['sessao']}"}


def _entrar(cliente, senha: str = SENHA, email: str = "eu@teste.com"):
    return cliente.post("/v1/conta/sessao", json={"email": email, "senha": senha})


def test_conta_com_senha_entra_por_email_e_a_chave_so_consulta(cliente, chave):
    sessao = _com_senha(cliente, chave)

    pela_chave = cliente.post("/v1/conta/chaves", json={"nome": "outra"}, headers=chave)
    consulta = cliente.get("/v1/conta", headers=chave)
    pela_sessao = cliente.post("/v1/conta/chaves", json={"nome": "outra"}, headers=sessao)

    assert pela_chave.status_code == 403, "a chave vazada não emite chave nem troca a senha"
    assert consulta.status_code == 200 and consulta.json()["dados"]["tem_senha"] is True
    assert pela_sessao.status_code == 201
    assert _entrar(cliente, "senha errada!").status_code == 401
    assert _entrar(cliente, email="EU@teste.com").status_code == 201


def test_sessao_nao_le_dado_e_sair_a_encerra(cliente, chave):
    sessao = _com_senha(cliente, chave)

    assert cliente.get("/v1/ativos", headers=sessao).status_code == 401, (
        "a sessão é da pessoa; dado é pela chave, que conta na cota"
    )
    assert cliente.delete("/v1/conta/sessao", headers=sessao).status_code == 204
    assert cliente.get("/v1/conta", headers=sessao).status_code == 401


def test_sessao_vencida_ou_de_conta_desativada_nao_entra(cliente, bancos, chave):
    sessao = _com_senha(cliente, chave)
    with bancos.acesso.begin() as conn:
        conn.execute(sa.text("UPDATE acesso.sessao SET expira_em = now() - interval '1 second'"))
    vencida = cliente.get("/v1/conta", headers=sessao).status_code

    nova = {"Authorization": f"Bearer {_entrar(cliente).json()['dados']['sessao']}"}
    conta_id = cliente.get("/v1/conta", headers=nova).json()["dados"]["id"]
    cliente.patch(f"/admin/contas/{conta_id}", json={"ativa": False}, headers=ADMIN)

    assert vencida == 401
    assert cliente.get("/v1/conta", headers=nova).status_code == 401
    assert _entrar(cliente).status_code == 401


def test_trocar_a_senha_pede_a_atual_e_derruba_as_outras_sessoes(cliente, chave):
    sessao = _com_senha(cliente, chave)
    outra = {"Authorization": f"Bearer {_entrar(cliente).json()['dados']['sessao']}"}

    sem_a_atual = cliente.put(
        "/v1/conta/senha", json={"senha": "outra senha longa"}, headers=sessao
    )
    trocada = cliente.put(
        "/v1/conta/senha", json={"senha": "outra senha longa", "atual": SENHA}, headers=sessao
    )

    assert sem_a_atual.status_code == 403, "sessão roubada não troca a senha sozinha"
    assert trocada.status_code == 200
    assert cliente.get("/v1/conta", headers=outra).status_code == 401
    assert _entrar(cliente).status_code == 401
    assert _entrar(cliente, "outra senha longa").status_code == 201


def test_senha_curta_e_recusada(cliente, chave):
    resposta = cliente.put("/v1/conta/senha", json={"senha": "curta"}, headers=chave)

    assert resposta.status_code == 422


def test_dez_senhas_erradas_bloqueiam_o_email_ate_a_certa(cliente, chave):
    _com_senha(cliente, chave)
    respostas = [
        cliente.post(
            "/v1/conta/sessao",
            json={"email": "eu@teste.com", "senha": "errada"},
            headers={"X-Forwarded-For": f"10.0.0.{i}"},
        ).status_code
        for i in range(10)
    ]

    assert respostas == [401] * 10
    assert _entrar(cliente).status_code == 429


def test_e_mail_sem_conta_e_senha_errada_respondem_igual(cliente, chave):
    _com_senha(cliente, chave)

    sem_conta = _entrar(cliente, email="ninguem@teste.com")
    errada = _entrar(cliente, "senha errada!")

    assert sem_conta.status_code == errada.status_code == 401
    assert sem_conta.json() == errada.json(), "a resposta não diz se o e-mail tem conta"


def test_a_base_guarda_a_senha_e_a_sessao_so_em_hash(cliente, bancos, chave):
    sessao = _com_senha(cliente, chave)["Authorization"][7:]

    with bancos.acesso.connect() as conn:
        senha = conn.execute(sa.text("SELECT senha_hash FROM acesso.conta")).scalar_one()
        guardada = conn.execute(sa.text("SELECT hash FROM acesso.sessao")).scalar_one()

    assert SENHA not in senha and acesso.senha_confere(SENHA, senha)
    assert guardada == acesso.hash_da_chave(sessao)


def test_administracao_redefine_a_senha_e_a_chave_volta_a_gerir_a_conta(cliente, chave):
    sessao = _com_senha(cliente, chave)
    conta_id = cliente.get("/v1/conta", headers=chave).json()["dados"]["id"]

    redefinida = cliente.delete(f"/admin/contas/{conta_id}/senha", headers=ADMIN)

    assert redefinida.status_code == 204
    assert cliente.get("/v1/conta", headers=sessao).status_code == 401
    assert _entrar(cliente).status_code == 401
    assert (
        cliente.put("/v1/conta/senha", json={"senha": SENHA}, headers=chave).status_code == 200
    ), "sem senha, a chave que o autor entrega é o que deixa a pessoa definir outra"
