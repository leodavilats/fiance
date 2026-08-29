from __future__ import annotations

import pytest

from app.core import ratelimit, usage
from app.core.config import get_settings
from tests.conftest import make_auth_headers


@pytest.fixture()
def rate_limit_on(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "rate_limit_enabled", True, raising=False)
    return settings


def test_contador_soma_na_janela_e_zera_na_seguinte():
    resource = "route:GET /teste"

    assert usage.increment("u_counter", resource, "2026-08-27T10:00", 120) == 1
    assert usage.increment("u_counter", resource, "2026-08-27T10:00", 120) == 2
    assert usage.current("u_counter", resource, "2026-08-27T10:00") == 2
    assert usage.current("u_counter", resource, "2026-08-27T10:01") == 0


def test_contador_e_por_usuario():
    resource = "feature:asset_page"
    usage.increment("u_tenant_a", resource, "2026-08", 60)

    assert usage.current("u_tenant_b", resource, "2026-08") == 0


def test_janela_mensal_usa_mes_brasileiro():
    from datetime import datetime

    from app.core.brt import BRT

    momento = datetime(2026, 9, 1, 0, 30, tzinfo=BRT).timestamp()

    assert usage.month_window(momento) == "2026-09"


def test_rota_cara_estoura_antes_da_rota_barata(client, rate_limit_on, monkeypatch):
    monkeypatch.setattr(ratelimit, "EXPENSIVE_PER_MINUTE", 3)
    headers = make_auth_headers("u_ratelimit")

    codigos = [client.get("/api/opportunities", headers=headers).status_code for _ in range(5)]

    assert 429 not in codigos[:3], "as três primeiras cabem no teto"
    assert codigos[3:] == [429, 429]


def test_resposta_429_diz_quando_tentar_de_novo(client, rate_limit_on, monkeypatch):
    monkeypatch.setattr(ratelimit, "EXPENSIVE_PER_MINUTE", 1)
    headers = make_auth_headers("u_retry_after")

    client.get("/api/opportunities", headers=headers)
    bloqueada = client.get("/api/opportunities", headers=headers)

    assert bloqueada.status_code == 429
    assert bloqueada.headers["Retry-After"] == "60"


def test_teto_de_um_usuario_nao_bloqueia_outro(client, rate_limit_on, monkeypatch):
    monkeypatch.setattr(ratelimit, "EXPENSIVE_PER_MINUTE", 1)
    abusador = make_auth_headers("u_abuse")
    inocente = make_auth_headers("u_innocent")

    client.get("/api/opportunities", headers=abusador)
    assert client.get("/api/opportunities", headers=abusador).status_code == 429
    assert client.get("/api/opportunities", headers=inocente).status_code != 429


def test_purga_remove_janela_vencida():
    usage.increment("u_purge", "route:GET /x", "2026-01-01T00:00", ttl_seconds=1)

    removidas = usage.purge_expired(now=2e10)

    assert removidas >= 1
    assert usage.current("u_purge", "route:GET /x", "2026-01-01T00:00") == 0
