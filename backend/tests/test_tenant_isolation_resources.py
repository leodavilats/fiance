import pytest

from tests.conftest import make_auth_headers

FIXED_INCOME = {
    "nome": "CDB Banco X",
    "tipo": "cdb",
    "valor_investido": 10_000.0,
    "taxa": 12.0,
    "tipo_taxa": "pre_fixado",
    "data_aplicacao": "2026-01-10",
    "vencimento": "2028-01-10",
    "liquidez": "no_vencimento",
}

DIVIDEND = {"ticker": "PETR4", "paid_at": "2026-08-01", "amount": 250.0, "kind": "dividendo"}

FOLLOWED = {
    "ticker": "PETR4",
    "source": "opportunities",
    "action": "comprar",
    "quantity": 10,
    "price": 30.0,
}


@pytest.fixture()
def two_users():
    return make_auth_headers("iso_owner"), make_auth_headers("iso_intruder")


def test_fixed_income_is_invisible_and_untouchable_across_tenants(client, two_users):
    owner, intruder = two_users

    created = client.post("/api/fixed-income", headers=owner, json=FIXED_INCOME)
    assert created.status_code == 201, created.text
    position_id = created.json()["id"]

    assert client.get("/api/fixed-income", headers=intruder).json()["items"] == []

    updated = client.put(
        f"/api/fixed-income/{position_id}", headers=intruder, json={"valor_investido": 1.0}
    )
    assert updated.status_code == 404

    assert client.delete(f"/api/fixed-income/{position_id}", headers=intruder).status_code == 404

    mine = client.get("/api/fixed-income", headers=owner).json()["items"]
    assert len(mine) == 1
    assert mine[0]["valor_investido"] == 10_000.0


def test_dividends_received_are_invisible_and_untouchable_across_tenants(client, two_users):
    owner, intruder = two_users

    created = client.post("/api/dividends/received", headers=owner, json=DIVIDEND)
    assert created.status_code == 201, created.text
    dividend_id = created.json()["id"]

    assert client.get("/api/dividends/received", headers=intruder).json()["items"] == []

    updated = client.put(
        f"/api/dividends/received/{dividend_id}", headers=intruder, json={"amount": 1.0}
    )
    assert updated.status_code == 404

    assert (
        client.delete(f"/api/dividends/received/{dividend_id}", headers=intruder).status_code == 404
    )

    mine = client.get("/api/dividends/received", headers=owner).json()["items"]
    assert len(mine) == 1
    assert mine[0]["amount"] == 250.0


def test_followed_suggestions_are_invisible_and_untouchable_across_tenants(client, two_users):
    owner, intruder = two_users

    created = client.post("/api/suggestions/followed", headers=owner, json=FOLLOWED)
    assert created.status_code == 201, created.text
    suggestion_id = created.json()["id"]

    assert client.get("/api/suggestions/followed", headers=intruder).json()["items"] == []

    assert (
        client.delete(f"/api/suggestions/followed/{suggestion_id}", headers=intruder).status_code
        == 404
    )

    assert len(client.get("/api/suggestions/followed", headers=owner).json()["items"]) == 1


def test_realized_trades_and_tax_balance_do_not_cross_tenants(client, two_users):
    owner, intruder = two_users

    client.post(
        "/api/portfolio/position",
        headers=owner,
        json={"ticker": "PETR4", "quantity": 100, "avg_price": 10.0, "category": "acoes_br"},
    )
    assert (
        client.post(
            "/api/portfolio/sell",
            headers=owner,
            json={"ticker": "PETR4", "quantity": 50, "sell_price": 30.0},
        ).status_code
        == 200
    )

    intruder_view = client.get("/api/portfolio/trades", headers=intruder).json()
    assert intruder_view["trades"] == []
    assert intruder_view.get("tax_loss_balances", []) == []

    assert len(client.get("/api/portfolio/trades", headers=owner).json()["trades"]) == 1


WRITE_ROUTES = [
    ("post", "/api/fixed-income", FIXED_INCOME),
    ("post", "/api/dividends/received", DIVIDEND),
    ("post", "/api/suggestions/followed", FOLLOWED),
    ("post", "/api/notifications/register-token", {"token": "x" * 40}),
    ("put", "/api/preferences", {"cash_available": 1.0}),
]


@pytest.mark.parametrize(("verb", "path", "body"), WRITE_ROUTES)
def test_write_routes_reject_anonymous_requests(client, verb, path, body):
    assert getattr(client, verb)(path, json=body).status_code == 401


@pytest.mark.parametrize(("verb", "path", "body"), WRITE_ROUTES)
def test_write_routes_reject_a_forged_token(client, verb, path, body):
    headers = {"Authorization": "Bearer nao.e.um.jwt"}
    assert getattr(client, verb)(path, json=body, headers=headers).status_code == 401


def test_token_signed_with_another_secret_is_rejected(client):
    import jwt

    forged = jwt.encode({"sub": "iso_owner", "exp": 4_102_444_800}, "outro-segredo", "HS256")
    resp = client.get("/api/portfolio", headers={"Authorization": f"Bearer {forged}"})
    assert resp.status_code == 401


def test_expired_token_is_rejected(client):
    import time

    import jwt

    from app.core.config import get_settings

    expired = jwt.encode(
        {"sub": "iso_owner", "exp": int(time.time()) - 10},
        get_settings().jwt_secret,
        "HS256",
    )
    resp = client.get("/api/portfolio", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401
