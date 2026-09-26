from __future__ import annotations

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

import app.core.auth as auth_mod
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.db_models import User

CLIENT_ID = "com.fiance.app"

_CHAVE = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _token(**claims) -> str:
    agora = int(time.time())
    corpo = {
        "iss": auth_mod.APPLE_ISSUER,
        "aud": CLIENT_ID,
        "sub": "000123.abc",
        "iat": agora,
        "exp": agora + 600,
        "email": "pessoa@exemplo.com",
        "email_verified": "true",
        "is_private_email": "false",
    }
    corpo.update(claims)
    return jwt.encode(corpo, _CHAVE, algorithm="RS256")


@pytest.fixture
def apple(monkeypatch):
    monkeypatch.setattr(get_settings(), "apple_client_id", CLIENT_ID)
    monkeypatch.setattr(auth_mod, "_apple_signing_key", lambda token: _CHAVE.public_key())


def _entrar(client, token: str, **extra):
    return client.post("/api/v1/auth/apple", json={"identity_token": token, **extra})


def test_login_com_apple_cria_conta_com_id_proprio(client, apple):
    resposta = _entrar(client, _token(), name="Pessoa")

    assert resposta.status_code == 200, resposta.text
    usuario = resposta.json()["user"]
    assert usuario["id"] == "apple:000123.abc", (
        "o id do Google é o sub puro: sem prefixo, um sub da Apple poderia cair na conta de outra "
        "pessoa"
    )
    assert usuario["name"] == "Pessoa", "a Apple só manda o nome no primeiro login"


@pytest.mark.parametrize(
    ("claims", "motivo"),
    [
        ({"aud": "outro.app"}, "audience de outro aplicativo"),
        ({"iss": "https://falso.example"}, "emissor que não é a Apple"),
        ({"exp": int(time.time()) - 10}, "token vencido"),
    ],
)
def test_token_que_nao_e_deste_app_e_recusado(client, apple, claims, motivo):
    assert _entrar(client, _token(**claims)).status_code == 401, motivo


def test_assinatura_de_outra_chave_e_recusada(client, apple):
    outra = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    forjado = jwt.encode(
        {"iss": auth_mod.APPLE_ISSUER, "aud": CLIENT_ID, "sub": "x", "iat": 1, "exp": 2**31},
        outra,
        algorithm="RS256",
    )

    assert _entrar(client, forjado).status_code == 401


def test_sem_client_id_configurado_falha_alto(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "apple_client_id", "")

    assert _entrar(client, _token()).status_code == 500


def test_email_confirmado_entra_na_conta_que_ja_existe(client, apple):
    session = SessionLocal()
    session.add(User(id="google-sub-1", email="mesma@exemplo.com", name="Já existe"))
    session.commit()
    session.close()

    resposta = _entrar(client, _token(sub="novo.sub", email="mesma@exemplo.com"))

    assert resposta.json()["user"]["id"] == "google-sub-1", (
        "a mesma pessoa, com o mesmo e-mail confirmado pela Apple, não pode ganhar uma segunda "
        "carteira vazia"
    )


def test_email_de_relay_privado_nao_liga_contas(client, apple):
    session = SessionLocal()
    session.add(User(id="google-sub-2", email="relay@privaterelay.appleid.com", name="Outra"))
    session.commit()
    session.close()

    resposta = _entrar(
        client,
        _token(sub="relay.sub", email="relay@privaterelay.appleid.com", is_private_email="true"),
    )

    usuario = resposta.json()["user"]
    assert usuario["id"] == "apple:relay.sub", (
        "relay privado não prova que é a mesma pessoa: não liga à conta que já usa o endereço"
    )
    assert usuario["email"] != "relay@privaterelay.appleid.com", (
        "o e-mail é único: repetir o de outra conta derrubaria o login com erro de servidor"
    )
