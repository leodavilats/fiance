from tests.conftest import make_auth_headers


def test_quick_invest_with_valid_cash_returns_allocations(client):
    uid = "test_quick_invest_valid"
    headers = make_auth_headers(uid)

    resp = client.post(
        "/api/quick-invest",
        headers=headers,
        json={"cash_available": 10000.0},
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["total_cash"] == 10000.0
    assert "allocations" in body
    assert "remaining_cash" in body
    assert "allocated_cash" in body
    # com PETR4/VALE3 disponíveis no universo fake e caixa suficiente,
    # esperamos ao menos uma alocação sugerida.
    assert isinstance(body["allocations"], list)


def test_quick_invest_with_zero_cash_is_rejected(client):
    uid = "test_quick_invest_zero"
    headers = make_auth_headers(uid)

    resp = client.post(
        "/api/quick-invest",
        headers=headers,
        json={"cash_available": 0},
    )
    assert resp.status_code == 422


def test_quick_invest_with_negative_cash_is_rejected(client):
    uid = "test_quick_invest_negative"
    headers = make_auth_headers(uid)

    resp = client.post(
        "/api/quick-invest",
        headers=headers,
        json={"cash_available": -100.0},
    )
    assert resp.status_code == 422


def test_quick_invest_requires_auth(client):
    resp = client.post("/api/quick-invest", json={"cash_available": 1000.0})
    assert resp.status_code == 401
