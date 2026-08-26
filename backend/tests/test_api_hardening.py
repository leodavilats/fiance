"""Regressões de segurança e de perda de dado (D3, D5, quick wins 1 e 2)."""

import pytest

from app.core.config import DEFAULT_JWT_SECRET, InsecureConfigurationError, Settings
from tests.conftest import make_auth_headers

ITEM = {"ticker": "PETR4", "quantity": 10, "avg_price": 30.0, "category": "auto"}


def test_cache_clear_requires_authentication(client):
    assert client.post("/api/cache/clear").status_code == 401


def test_cache_clear_works_when_authenticated(client):
    headers = make_auth_headers("cache_clear_user")
    assert client.post("/api/cache/clear", headers=headers).status_code == 200


def test_startup_validation_rejects_default_jwt_secret_outside_development():
    settings = Settings(app_env="production", jwt_secret=DEFAULT_JWT_SECRET)
    with pytest.raises(InsecureConfigurationError):
        settings.validate_for_startup()


def test_startup_validation_allows_default_secret_in_development():
    Settings(app_env="development", jwt_secret=DEFAULT_JWT_SECRET).validate_for_startup()


def test_startup_validation_accepts_configured_secret():
    Settings(
        app_env="production",
        jwt_secret="um-segredo-de-verdade-com-tamanho-suficiente",
        allowed_origins="https://app.exemplo.com",
    ).validate_for_startup()


def test_wildcard_cors_never_allows_credentials():
    dev = Settings(app_env="development")
    assert dev.cors_origins == ["*"]
    assert dev.cors_allow_credentials is False


def test_put_preferences_preserves_cash_available(client):
    headers = make_auth_headers("prefs_cash_user")

    client.put("/api/preferences", headers=headers, json={"cash_available": 7500.0})

    resp = client.put("/api/preferences", headers=headers, json={"desired_yield_fii": 0.12})
    assert resp.status_code == 200
    assert resp.json()["cash_available"] == 7500.0
    assert resp.json()["desired_yield_fii"] == 0.12

    assert client.get("/api/preferences", headers=headers).json()["cash_available"] == 7500.0


def test_put_preferences_round_trips_cash_available(client):
    headers = make_auth_headers("prefs_cash_roundtrip")
    client.put("/api/preferences", headers=headers, json={"cash_available": 100.5})
    assert client.get("/api/preferences", headers=headers).json()["cash_available"] == 100.5


def test_put_portfolio_rejects_empty_list_instead_of_wiping(client):
    headers = make_auth_headers("wipe_guard_user")
    client.put("/api/portfolio", headers=headers, json={"items": [ITEM]})

    resp = client.put("/api/portfolio", headers=headers, json={"items": []})
    assert resp.status_code == 422

    items = client.get("/api/portfolio", headers=headers).json()["items"]
    assert [i["ticker"] for i in items] == ["PETR4"]


def test_upsert_position_does_not_touch_other_positions(client):
    headers = make_auth_headers("upsert_user")
    client.put(
        "/api/portfolio",
        headers=headers,
        json={
            "items": [
                ITEM,
                {"ticker": "VALE3", "quantity": 5, "avg_price": 60.0, "category": "auto"},
            ]
        },
    )

    resp = client.post(
        "/api/portfolio/position",
        headers=headers,
        json={"ticker": "ITUB4", "quantity": 20, "avg_price": 28.0, "category": "auto"},
    )
    assert resp.status_code == 200
    assert {i["ticker"] for i in resp.json()["items"]} == {"PETR4", "VALE3", "ITUB4"}


def test_upsert_position_updates_existing_quantity(client):
    headers = make_auth_headers("upsert_update_user")
    client.post("/api/portfolio/position", headers=headers, json=ITEM)
    client.post(
        "/api/portfolio/position",
        headers=headers,
        json={**ITEM, "quantity": 42},
    )
    items = client.get("/api/portfolio", headers=headers).json()["items"]
    assert len(items) == 1
    assert items[0]["quantity"] == 42


def test_portfolio_rejects_oversized_collections(client):
    headers = make_auth_headers("oversize_user")
    resp = client.post(
        "/api/portfolio/evaluate",
        headers=headers,
        json={"items": [ITEM] * 10_000},
    )
    assert resp.status_code == 422


def test_portfolio_rejects_malformed_ticker(client):
    headers = make_auth_headers("bad_ticker_user")
    resp = client.post(
        "/api/portfolio/position",
        headers=headers,
        json={"ticker": "../../etc/passwd", "quantity": 1, "avg_price": 1.0},
    )
    assert resp.status_code == 422


def test_sell_rejects_future_sold_at(client):
    import time

    headers = make_auth_headers("future_sell_user")
    client.post("/api/portfolio/position", headers=headers, json=ITEM)

    resp = client.post(
        "/api/portfolio/sell",
        headers=headers,
        json={
            "ticker": "PETR4",
            "quantity": 1,
            "sell_price": 40.0,
            "sold_at": time.time() + 60 * 24 * 3600,
        },
    )
    assert resp.status_code == 400


def test_sell_rejects_far_backdated_sold_at(client):
    import time

    headers = make_auth_headers("backdated_sell_user")
    client.post("/api/portfolio/position", headers=headers, json=ITEM)

    resp = client.post(
        "/api/portfolio/sell",
        headers=headers,
        json={
            "ticker": "PETR4",
            "quantity": 1,
            "sell_price": 40.0,
            "sold_at": time.time() - 400 * 24 * 3600,
        },
    )
    assert resp.status_code == 400


def test_cache_clear_is_open_to_any_session_only_in_development(monkeypatch):
    import pytest as _pytest
    from fastapi import HTTPException

    from app.core import auth as auth_mod
    from app.core.config import Settings

    async def _call(settings: Settings, user_id: str) -> str:
        monkeypatch.setattr(auth_mod, "get_settings", lambda: settings)
        return await auth_mod.require_admin(user_id)

    import asyncio

    dev = Settings(app_env="development")
    assert asyncio.run(_call(dev, "qualquer_um")) == "qualquer_um"

    prod = Settings(app_env="production", jwt_secret="s" * 40, allowed_origins="https://x.com")
    with _pytest.raises(HTTPException) as exc:
        asyncio.run(_call(prod, "qualquer_um"))
    assert exc.value.status_code == 403

    with_allowlist = Settings(
        app_env="production",
        jwt_secret="s" * 40,
        allowed_origins="https://x.com",
        admin_user_ids="operador_1, operador_2",
    )
    assert asyncio.run(_call(with_allowlist, "operador_2")) == "operador_2"
    with _pytest.raises(HTTPException) as exc:
        asyncio.run(_call(with_allowlist, "operador_3"))
    assert exc.value.status_code == 403


def test_alert_rejects_ticker_that_is_not_a_b3_symbol(client):
    headers = make_auth_headers("alert_ticker_user")
    resp = client.post(
        "/api/alerts",
        headers=headers,
        json={"ticker": "../../etc/passwd", "condition": "below", "target_price": 10.0},
    )
    assert resp.status_code == 422


def test_alert_rejects_implausible_target_price(client):
    headers = make_auth_headers("alert_price_user")
    resp = client.post(
        "/api/alerts",
        headers=headers,
        json={"ticker": "PETR4", "condition": "below", "target_price": 1e12},
    )
    assert resp.status_code == 422


def test_alert_creation_stops_at_the_per_user_ceiling(client):
    from app.api.alerts import MAX_ALERTS_PER_USER

    headers = make_auth_headers("alert_ceiling_user")
    body = {"ticker": "PETR4", "condition": "below", "target_price": 10.0}

    for _ in range(MAX_ALERTS_PER_USER):
        assert client.post("/api/alerts", headers=headers, json=body).status_code == 201

    resp = client.post("/api/alerts", headers=headers, json=body)
    assert resp.status_code == 409
    assert "Limite" in resp.json()["detail"]
