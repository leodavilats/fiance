from __future__ import annotations

import sqlalchemy as sa

from dadosapi import acesso
from tests.conftest import TOKEN, criar_conta


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
