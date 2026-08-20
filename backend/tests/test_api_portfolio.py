from tests.conftest import make_auth_headers


def test_portfolio_crud_flow(client):
    uid = "test_portfolio_crud"
    headers = make_auth_headers(uid)

    resp = client.get("/api/portfolio", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["items"] == []

    resp = client.put(
        "/api/portfolio",
        headers=headers,
        json={
            "items": [{"ticker": "PETR4", "quantity": 100, "avg_price": 30.0, "category": "auto"}]
        },
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["ticker"] == "PETR4"

    resp = client.get("/api/portfolio", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1

    resp = client.put(
        "/api/portfolio",
        headers=headers,
        json={
            "items": [
                {"ticker": "PETR4", "quantity": 50, "avg_price": 32.0, "category": "auto"},
                {"ticker": "VALE3", "quantity": 20, "avg_price": 55.0, "category": "auto"},
            ]
        },
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert {i["ticker"] for i in items} == {"PETR4", "VALE3"}

    resp = client.delete("/api/portfolio/VALE3", headers=headers)
    assert resp.status_code == 200

    resp = client.get("/api/portfolio", headers=headers)
    tickers = {i["ticker"] for i in resp.json()["items"]}
    assert tickers == {"PETR4"}


def test_portfolio_sell_partial_then_total_and_closed_trades(client):
    uid = "test_portfolio_sell_http"
    headers = make_auth_headers(uid)

    client.put(
        "/api/portfolio",
        headers=headers,
        json={
            "items": [{"ticker": "PETR4", "quantity": 100, "avg_price": 10.0, "category": "auto"}]
        },
    )

    resp = client.post(
        "/api/portfolio/sell",
        headers=headers,
        json={"ticker": "PETR4", "quantity": 40, "sell_price": 15.0},
    )
    assert resp.status_code == 200
    trade = resp.json()
    assert trade["quantity"] == 40
    assert trade["gross_profit"] == (15.0 - 10.0) * 40

    resp = client.get("/api/portfolio", headers=headers)
    remaining = [i for i in resp.json()["items"] if i["ticker"] == "PETR4"][0]
    assert remaining["quantity"] == 60

    resp = client.post(
        "/api/portfolio/sell",
        headers=headers,
        json={"ticker": "PETR4", "quantity": 60, "sell_price": 20.0},
    )
    assert resp.status_code == 200

    resp = client.get("/api/portfolio", headers=headers)
    assert resp.json()["items"] == []

    resp = client.get("/api/portfolio/trades", headers=headers)
    assert resp.status_code == 200
    trades_body = resp.json()
    assert len(trades_body["trades"]) == 2
    assert trades_body["total_realized_pnl"] == sum(t["net_profit"] for t in trades_body["trades"])


def test_portfolio_sell_more_than_owned_returns_4xx(client):
    uid = "test_portfolio_sell_too_much_http"
    headers = make_auth_headers(uid)

    client.put(
        "/api/portfolio",
        headers=headers,
        json={
            "items": [{"ticker": "ITUB4", "quantity": 10, "avg_price": 20.0, "category": "auto"}]
        },
    )

    resp = client.post(
        "/api/portfolio/sell",
        headers=headers,
        json={"ticker": "ITUB4", "quantity": 999, "sell_price": 25.0},
    )
    assert 400 <= resp.status_code < 500


def test_portfolio_sell_unknown_ticker_returns_4xx(client):
    uid = "test_portfolio_sell_unknown_http"
    headers = make_auth_headers(uid)

    resp = client.post(
        "/api/portfolio/sell",
        headers=headers,
        json={"ticker": "NOPE99", "quantity": 1, "sell_price": 1.0},
    )
    assert 400 <= resp.status_code < 500


def test_portfolio_endpoints_require_auth(client):
    assert client.get("/api/portfolio").status_code == 401
    valid_item = {"ticker": "PETR4", "quantity": 1, "avg_price": 1.0, "category": "auto"}
    assert client.put("/api/portfolio", json={"items": [valid_item]}).status_code == 401
    assert client.post("/api/portfolio/position", json=valid_item).status_code == 401
    assert client.delete("/api/portfolio/position/PETR4").status_code == 401
    assert client.delete("/api/portfolio/PETR4").status_code == 401
    assert (
        client.post(
            "/api/portfolio/sell", json={"ticker": "PETR4", "quantity": 1, "sell_price": 1}
        ).status_code
        == 401
    )
    assert client.get("/api/portfolio/trades").status_code == 401
