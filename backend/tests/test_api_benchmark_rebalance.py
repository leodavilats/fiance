from tests.conftest import make_auth_headers


def test_benchmark_empty_without_snapshots(client):
    headers = make_auth_headers("test_benchmark_empty")

    resp = client.get("/api/benchmark", headers=headers)
    assert resp.status_code == 200

    body = resp.json()
    assert body["points"] == []
    assert body["ibov_available"] is False


def test_benchmark_requires_auth(client):
    resp = client.get("/api/benchmark")
    assert resp.status_code == 401


def test_rebalance_no_goals_no_gap(client):
    headers = make_auth_headers("test_rebalance_empty")

    resp = client.get("/api/rebalance", headers=headers)
    assert resp.status_code == 200

    body = resp.json()
    assert "needs_rebalance" in body
    assert "allocations" in body
    assert body["suggestions"] == [] or isinstance(body["suggestions"], list)


def test_rebalance_requires_auth(client):
    resp = client.get("/api/rebalance")
    assert resp.status_code == 401


def test_compare_requires_tickers(client):
    headers = make_auth_headers("test_compare_empty")

    resp = client.get("/api/compare", params={"tickers": ""}, headers=headers)
    assert resp.status_code == 400


def test_compare_requires_auth(client):
    resp = client.get("/api/compare", params={"tickers": "PETR4"})
    assert resp.status_code == 401
