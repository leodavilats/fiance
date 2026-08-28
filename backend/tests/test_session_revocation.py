"""Sessão: claims obrigatórias, revogação de servidor e rotação de refresh."""

from __future__ import annotations

import time

import jwt
import pytest

from app.core.auth import (
    ACCESS_TTL_SECONDS,
    JWT_ALGORITHM,
    REFRESH_TTL_SECONDS,
    issue_access_token,
    issue_refresh_token,
)
from app.core.config import get_settings
from tests.conftest import make_auth_headers


def _sign(payload: dict) -> str:
    return jwt.encode(payload, get_settings().jwt_secret, algorithm=JWT_ALGORITHM)


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_token_sem_sub_devolve_401_e_nao_500(client):
    """Antes disso o KeyError virava erro interno — e erro de auth é 401."""
    now = int(time.time())
    token = _sign({"iat": now, "exp": now + 600})

    response = client.get("/api/auth/me", headers=_headers(token))

    assert response.status_code == 401


@pytest.mark.parametrize("missing", ["exp", "iat"])
def test_token_sem_claim_obrigatoria_e_rejeitado(client, missing):
    now = int(time.time())
    payload = {"sub": "u_claims", "iat": now, "exp": now + 600}
    payload.pop(missing)

    response = client.get("/api/auth/me", headers=_headers(_sign(payload)))

    assert response.status_code == 401


def test_refresh_nao_serve_como_acesso(client):
    """Trocar o tipo de token não pode virar escalada de sessão."""
    response = client.get("/api/auth/me", headers=_headers(issue_refresh_token("u_typ")))

    assert response.status_code == 401


def test_acesso_nao_serve_como_refresh(client):
    response = client.post(
        "/api/auth/refresh", json={"refresh_token": issue_access_token("u_typ2")}
    )

    assert response.status_code == 401


def test_logout_invalida_o_token_no_servidor(client):
    headers = make_auth_headers("u_logout")

    assert client.get("/api/auth/me", headers=headers).status_code in (200, 404)
    assert client.post("/api/auth/logout", json={}, headers=headers).status_code == 200

    depois = client.get("/api/auth/me", headers=headers)
    assert depois.status_code == 401


def test_refresh_rotaciona_e_queima_o_refresh_usado(client):
    refresh = issue_refresh_token("u_rot")

    primeira = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert primeira.status_code == 200
    body = primeira.json()
    assert body["expires_in"] == ACCESS_TTL_SECONDS
    assert body["refresh_token"] != refresh

    segunda = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert segunda.status_code == 401, "refresh reapresentado tem que cair na denylist"

    novo = client.post("/api/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert novo.status_code == 200


def test_logout_de_todos_os_dispositivos_corta_sessoes_antigas(client):
    """O carimbo em `tokens_valid_from` mata token que a denylist nem conhece."""
    dispositivo_a = make_auth_headers("u_all")
    time.sleep(1.1)
    dispositivo_b = make_auth_headers("u_all")

    assert (
        client.post(
            "/api/auth/logout", json={"all_devices": True}, headers=dispositivo_b
        ).status_code
        == 200
    )

    assert client.get("/api/auth/me", headers=dispositivo_a).status_code == 401
    assert client.get("/api/auth/me", headers=dispositivo_b).status_code == 401


def test_token_legado_de_30_dias_continua_valendo(client):
    """O emissor antigo não punha `typ` nem `jti`; derrubá-lo deslogaria a base."""
    now = int(time.time())
    legado = _sign({"sub": "u_legado", "iat": now, "exp": now + REFRESH_TTL_SECONDS})

    response = client.get("/api/portfolio", headers=_headers(legado))

    assert response.status_code == 200


def test_ttl_do_acesso_e_curto():
    """TTL curto é o que dá efeito prático à revogação — uma hora, não um mês."""
    assert ACCESS_TTL_SECONDS <= 3600
    assert REFRESH_TTL_SECONDS >= 7 * 24 * 3600
