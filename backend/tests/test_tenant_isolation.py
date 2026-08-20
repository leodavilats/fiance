"""Isolamento entre tenants — a garantia central do produto.

Cada teste da suíte usava um user_id distinto, mas nenhum verificava que o
usuário A não vê o dado de B, nem que B não consegue apagar recurso de A.
"""

from tests.conftest import make_auth_headers

ITEM_A = {"ticker": "PETR4", "quantity": 100, "avg_price": 30.0, "category": "auto"}


def _seed_user_a(client, headers_a):
    client.put("/api/portfolio", headers=headers_a, json={"items": [ITEM_A]})
    client.put(
        "/api/goals",
        headers=headers_a,
        json={"goals": [{"category": "acoes_br", "target_pct": 80.0}]},
    )
    client.put("/api/preferences", headers=headers_a, json={"cash_available": 12345.0})
    created = client.post(
        "/api/alerts",
        headers=headers_a,
        json={"ticker": "PETR4", "condition": "below", "target_price": 20.0},
    )
    assert created.status_code == 201
    return created.json()["id"]


def test_user_b_sees_none_of_user_a_data(client):
    headers_a = make_auth_headers("tenant_a")
    headers_b = make_auth_headers("tenant_b")

    _seed_user_a(client, headers_a)

    assert client.get("/api/portfolio", headers=headers_b).json()["items"] == []
    assert client.get("/api/alerts", headers=headers_b).json() == []
    assert client.get("/api/portfolio/trades", headers=headers_b).json()["trades"] == []
    assert client.get("/api/preferences", headers=headers_b).json()["cash_available"] == 0.0

    # A continua vendo o que cadastrou.
    items_a = client.get("/api/portfolio", headers=headers_a).json()["items"]
    assert [i["ticker"] for i in items_a] == ["PETR4"]


def test_user_b_cannot_delete_alert_of_user_a(client):
    headers_a = make_auth_headers("tenant_a_alert")
    headers_b = make_auth_headers("tenant_b_alert")

    alert_id = _seed_user_a(client, headers_a)

    assert client.delete(f"/api/alerts/{alert_id}", headers=headers_b).status_code == 404

    # O alerta de A segue existindo depois da tentativa de B.
    ids_a = [a["id"] for a in client.get("/api/alerts", headers=headers_a).json()]
    assert alert_id in ids_a


def test_user_b_cannot_delete_or_sell_position_of_user_a(client):
    headers_a = make_auth_headers("tenant_a_pos")
    headers_b = make_auth_headers("tenant_b_pos")

    _seed_user_a(client, headers_a)

    # DELETE é idempotente, mas não pode alcançar a linha de outro tenant.
    client.delete("/api/portfolio/position/PETR4", headers=headers_b)
    assert (
        client.post(
            "/api/portfolio/sell",
            headers=headers_b,
            json={"ticker": "PETR4", "quantity": 1, "sell_price": 40.0},
        ).status_code
        == 404
    )

    items_a = client.get("/api/portfolio", headers=headers_a).json()["items"]
    assert [i["ticker"] for i in items_a] == ["PETR4"]
    assert items_a[0]["quantity"] == 100


def test_user_b_goals_are_defaults_not_user_a_goals(client):
    headers_a = make_auth_headers("tenant_a_goals")
    headers_b = make_auth_headers("tenant_b_goals")

    _seed_user_a(client, headers_a)

    goals_b = {
        g["category"]: g["target_pct"] for g in client.get("/api/goals", headers=headers_b).json()
    }
    assert goals_b.get("acoes_br") != 80.0
