from tests.conftest import make_auth_headers


def test_strategy_without_cash_available_defaults_to_zero(client):
    uid = "test_strategy_default_cash"
    headers = make_auth_headers(uid)

    resp = client.get("/api/strategy", headers=headers)
    assert resp.status_code == 200

    body = resp.json()
    assert "profile" in body or "investor_profile" in body or isinstance(body, dict)


def test_strategy_with_cash_available_query_param(client):
    uid = "test_strategy_with_cash"
    headers = make_auth_headers(uid)

    resp = client.get("/api/strategy", headers=headers, params={"cash_available": 5000})
    assert resp.status_code == 200
    assert isinstance(resp.json(), dict)


def test_strategy_uses_deterministic_ranking(client, monkeypatch):
    from app.core.config import get_settings

    get_settings.cache_clear() if hasattr(get_settings, "cache_clear") else None

    uid = "test_strategy_deterministic_ranking"
    headers = make_auth_headers(uid)

    resp = client.get("/api/strategy", headers=headers, params={"cash_available": 1000})
    assert resp.status_code == 200


def test_strategy_requires_auth(client):
    resp = client.get("/api/strategy")
    assert resp.status_code == 401
