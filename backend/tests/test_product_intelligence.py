import pytest

from app.services.benchmark_service import _twr_series
from app.services.snapshot_job import record_snapshot_for_user
from app.storage import portfolio_store
from tests.conftest import make_auth_headers

ITEM = {"ticker": "PETR4", "quantity": 100, "avg_price": 30.0, "category": "auto"}


def _cdb(**overrides) -> dict:
    body = {
        "nome": "CDB Banco X",
        "tipo": "cdb",
        "valor_investido": 20000.0,
        "taxa": 13.0,
        "tipo_taxa": "pre_fixado",
        "data_aplicacao": "2025-02-01",
    }
    body.update(overrides)
    return body


def test_pure_contribution_yields_zero_return():
    snapshots = [
        {"total_invested": 10_000.0, "total_current": 10_000.0},
        {"total_invested": 20_000.0, "total_current": 20_000.0},
    ]

    series = _twr_series(snapshots)
    assert series[-1] == pytest.approx(0.0, abs=1e-6)


def test_real_gain_is_captured_even_with_a_contribution():
    snapshots = [
        {"total_invested": 10_000.0, "total_current": 10_000.0},
        {"total_invested": 20_000.0, "total_current": 21_000.0},
    ]

    series = _twr_series(snapshots)
    assert series[-1] == pytest.approx(10.0, abs=0.01)


def test_withdrawal_does_not_look_like_a_loss():
    snapshots = [
        {"total_invested": 20_000.0, "total_current": 20_000.0},
        {"total_invested": 10_000.0, "total_current": 10_000.0},
    ]

    assert _twr_series(snapshots)[-1] == pytest.approx(0.0, abs=1e-6)


def test_returns_compound_across_periods():
    snapshots = [
        {"total_invested": 100.0, "total_current": 100.0},
        {"total_invested": 100.0, "total_current": 110.0},
        {"total_invested": 100.0, "total_current": 121.0},
    ]

    assert _twr_series(snapshots)[-1] == pytest.approx(21.0, abs=0.01)


def test_empty_opening_portfolio_does_not_divide_by_zero():
    snapshots = [
        {"total_invested": 0.0, "total_current": 0.0},
        {"total_invested": 5_000.0, "total_current": 5_000.0},
    ]

    assert _twr_series(snapshots)[-1] == pytest.approx(0.0, abs=1e-6)


@pytest.mark.anyio
async def test_benchmark_endpoint_reports_the_method_and_contributions(client):
    uid = "benchmark_twr"
    headers = make_auth_headers(uid)
    client.put("/api/portfolio", headers=headers, json={"items": [ITEM]})

    portfolio_store.record_snapshot(
        total_invested=1000.0, total_current=1000.0, total_pnl=0.0, total_pnl_pct=0.0, user_id=uid
    )
    with portfolio_store._session_global() as session:
        from app.models.db_models import PortfolioSnapshot

        row = session.scalars(
            session.query(PortfolioSnapshot).filter_by(user_id=uid).statement
        ).first()
        row.captured_at -= 5 * 86400

    await record_snapshot_for_user(uid)

    body = client.get("/api/benchmark", headers=headers).json()
    assert body["method"] == "twr"
    assert len(body["points"]) == 2
    assert "net_contributions" in body
    assert body["points"][0]["invested"] == 1000.0


def test_whats_new_requires_auth(client):
    assert client.get("/api/whats-new").status_code == 401


def test_whats_new_always_answers_with_an_action(client):
    headers = make_auth_headers("whats_new_empty")
    body = client.get("/api/whats-new", headers=headers).json()

    assert body["items"], "sempre deve haver ao menos uma linha"
    for item in body["items"]:
        assert item["action"], f"linha sem ação: {item['kind']}"
        assert item["action_label"]
        assert item["title"] and item["detail"]


def test_whats_new_falls_back_to_an_explicit_empty_line(client, monkeypatch):
    from app.services.whats_new_service import WhatsNewService

    async def no_opportunities(self, positions):
        return []

    monkeypatch.setattr(WhatsNewService, "_opportunity_items", no_opportunities)

    headers = make_auth_headers("whats_new_truly_empty")
    body = client.get("/api/whats-new", headers=headers).json()

    assert len(body["items"]) == 1
    assert body["items"][0]["kind"] == "empty"
    assert body["items"][0]["action"]


def test_whats_new_surfaces_upcoming_maturity(client):
    from datetime import UTC, datetime, timedelta

    headers = make_auth_headers("whats_new_maturity")
    hoje = datetime.now(UTC).date()
    client.post(
        "/api/fixed-income",
        headers=headers,
        json=_cdb(vencimento=(hoje + timedelta(days=10)).isoformat()),
    )

    items = client.get("/api/whats-new", headers=headers).json()["items"]
    maturity = [i for i in items if i["kind"] == "maturity"]
    assert maturity
    assert maturity[0]["action"] == "fixed_income"


def test_whats_new_surfaces_realized_losses_for_tax_offset(client):
    headers = make_auth_headers("whats_new_tax")
    client.post("/api/portfolio/position", headers=headers, json=ITEM)
    client.post(
        "/api/portfolio/sell",
        headers=headers,
        json={"ticker": "PETR4", "quantity": 100, "sell_price": 20.0},
    )

    items = client.get("/api/whats-new", headers=headers).json()["items"]
    tax = [i for i in items if i["kind"] == "tax"]
    assert tax
    assert "compensar" in tax[0]["title"].lower()


def test_whats_new_caps_the_number_of_lines(client):
    headers = make_auth_headers("whats_new_cap")
    client.put("/api/portfolio", headers=headers, json={"items": [ITEM]})
    client.post("/api/fixed-income", headers=headers, json=_cdb())

    body = client.get("/api/whats-new", headers=headers).json()
    assert 1 <= len(body["items"]) <= 5


def test_alerts_are_grouped_capped_and_actionable(client):
    headers = make_auth_headers("alerts_grouped")
    client.put(
        "/api/portfolio",
        headers=headers,
        json={
            "items": [
                ITEM,
                {"ticker": "VALE3", "quantity": 10, "avg_price": 60.0, "category": "auto"},
            ]
        },
    )

    alerts = client.get("/api/dashboard", headers=headers).json()["alerts"]
    assert len(alerts) <= 4

    for alert in alerts:
        assert alert["count"] >= 1
        assert alert["action"], f"alerta sem ação: {alert['kind']}"
        assert alert["action_label"]


def test_dashboard_reports_data_freshness(client):
    headers = make_auth_headers("freshness_user")
    client.put("/api/portfolio", headers=headers, json={"items": [ITEM]})

    freshness = client.get("/api/dashboard", headers=headers).json()["freshness"]
    assert freshness is not None
    assert freshness["rates_source"] in ("bcb", "estimativa")
    assert freshness["quotes_ttl_seconds"] > 0


def test_positions_carry_verdict_provenance(client):
    headers = make_auth_headers("provenance_positions")
    client.put("/api/portfolio", headers=headers, json={"items": [ITEM]})

    positions = client.get("/api/dashboard", headers=headers).json()["positions"]
    petr = next(p for p in positions if p["ticker"] == "PETR4")

    for field in ("confidence", "data_years", "consensus_methods", "trend_basis"):
        assert field in petr

    assert petr["confidence"] > 0
    assert petr["data_years"] > 0


def test_score_reports_data_completeness(client):
    headers = make_auth_headers("completeness_user")
    items = client.get(
        "/api/opportunities", headers=headers, params={"include_held": "true"}
    ).json()["items"]

    assert items
    for item in items:
        assert 0.0 <= item["data_completeness"] <= 1.0
        assert "data_completeness" in item["score_breakdown"]

    by_ticker = {i["ticker"]: i for i in items}
    assert by_ticker["VALE3"]["data_completeness"] < by_ticker["PETR4"]["data_completeness"]
