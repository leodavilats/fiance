from app.storage import portfolio_store
from tests.conftest import make_auth_headers


def test_dashboard_without_positions(client):
    uid = "test_dash_empty"
    headers = make_auth_headers(uid)

    resp = client.get("/api/dashboard", headers=headers)
    assert resp.status_code == 200

    body = resp.json()
    assert body["positions"] == []
    assert "summary" in body
    assert "cash_available" not in body["summary"]


def test_dashboard_with_positions(client):
    uid = "test_dash_with_positions"
    portfolio_store.upsert_position("PETR4", quantity=100, avg_price=30.0, user_id=uid)
    headers = make_auth_headers(uid)

    resp = client.get("/api/dashboard", headers=headers)
    assert resp.status_code == 200

    body = resp.json()
    assert len(body["positions"]) == 1
    pos = body["positions"][0]
    assert pos["ticker"] == "PETR4"
    assert pos["quantity"] == 100


def test_dashboard_contract_summary_fields(client):
    """Contrato: web/mobile leem DashboardSummary sem 'cash_available' (removido
    deliberadamente — ver KNOWN_ISSUES/histórico). Se o campo reaparecer sem
    querer, este teste falha e evita uma regressão silenciosa de contrato."""
    uid = "test_dash_contract"
    headers = make_auth_headers(uid)

    resp = client.get("/api/dashboard", headers=headers)
    assert resp.status_code == 200

    summary = resp.json()["summary"]
    expected_fields = {
        "total_invested",
        "total_current",
        "total_pnl",
        "total_pnl_pct",
        "monthly_dividends_estimate",
    }
    assert expected_fields.issubset(summary.keys())
    assert "cash_available" not in summary

    body = resp.json()
    for key in (
        "summary",
        "positions",
        "top_buys",
        "top_sells",
        "alerts",
        "allocations",
        "snapshots",
    ):
        assert key in body


def test_dashboard_requires_auth(client):
    resp = client.get("/api/dashboard")
    assert resp.status_code == 401
