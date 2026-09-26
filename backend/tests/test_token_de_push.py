from __future__ import annotations

import pytest

from app.storage import portfolio_store
from tests.conftest import make_auth_headers

ROTA = "/api/notifications/register-token"


def _token_fcm(semente: str) -> str:
    return f"{semente}:APA91b" + "Xy_-9" * 28


def _tokens_de(user_id: str) -> list[str]:
    return [t["token"] for t in portfolio_store.list_device_tokens(user_id=user_id)]


@pytest.mark.parametrize(
    "token",
    [
        "abc",
        "x" * 31,
        "x" * 513,
        "token com espaço" + "x" * 40,
        "<script>" + "x" * 40,
        "",
    ],
)
def test_registro_recusa_o_que_nao_tem_forma_de_token_fcm(client, token):
    headers = make_auth_headers("push_lixo")

    resposta = client.post(ROTA, headers=headers, json={"token": token})

    assert resposta.status_code == 422, (
        "o token vai para o FCM e fica ligado a uma conta: o que não tem a forma de um "
        "token de instalação não pode ser gravado"
    )
    assert _tokens_de("push_lixo") == []


def test_registro_recusa_plataforma_fora_do_vocabulario(client):
    headers = make_auth_headers("push_plataforma")

    resposta = client.post(ROTA, headers=headers, json={"token": _token_fcm("p"), "platform": "x"})

    assert resposta.status_code == 422, "plataforma é vocabulário fechado, não texto livre"


def test_registro_aceita_um_token_fcm_real(client):
    headers = make_auth_headers("push_real")

    resposta = client.post(ROTA, headers=headers, json={"token": _token_fcm("fReal")})

    assert resposta.status_code == 204
    assert _tokens_de("push_real") == [_token_fcm("fReal")]


def test_remocao_aplica_a_mesma_regra_do_registro(client):
    headers = make_auth_headers("push_remocao")

    assert client.delete(ROTA, headers=headers, params={"token": "abc"}).status_code == 422, (
        "registro e remoção descrevem o mesmo objeto, e a regra de forma é uma só"
    )


def test_trocar_de_conta_no_mesmo_aparelho_leva_o_token(client):
    token = _token_fcm("aparelho")
    client.post(ROTA, headers=make_auth_headers("push_conta_a"), json={"token": token})
    client.post(ROTA, headers=make_auth_headers("push_conta_b"), json={"token": token})

    assert _tokens_de("push_conta_a") == [], (
        "o token identifica a instalação: a conta que entrou por último é a que recebe o "
        "aviso, e a anterior não pode seguir recebendo alerta de outra carteira"
    )
    assert _tokens_de("push_conta_b") == [token]


def test_remocao_por_outra_conta_nao_apaga_o_token_do_dono(client):
    token = _token_fcm("dono")
    client.post(ROTA, headers=make_auth_headers("push_dono"), json={"token": token})

    client.delete(ROTA, headers=make_auth_headers("push_intruso"), params={"token": token})

    assert _tokens_de("push_dono") == [token], "a remoção é escopada por quem pede"


def test_sair_de_todos_os_aparelhos_apaga_os_tokens_da_conta(client):
    headers = make_auth_headers("push_todos")
    outro = _token_fcm("outraConta")
    client.post(ROTA, headers=headers, json={"token": _token_fcm("um")})
    client.post(ROTA, headers=headers, json={"token": _token_fcm("dois")})
    client.post(ROTA, headers=make_auth_headers("push_vizinho"), json={"token": outro})

    resposta = client.post("/api/auth/logout", json={"all_devices": True}, headers=headers)

    assert resposta.status_code == 200
    assert _tokens_de("push_todos") == [], (
        "sessão cortada em todo aparelho não pode deixar aparelho recebendo aviso da carteira"
    )
    assert _tokens_de("push_vizinho") == [outro], "o corte é da conta, não da tabela"
