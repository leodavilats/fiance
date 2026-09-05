from datetime import UTC, datetime, timedelta

import pytest

from app.core.brt import BRT, month_key, month_start_timestamp
from app.ledger.apuracao import apurar
from app.ledger.entries import LedgerEntry, TransactionKind
from tests.conftest import make_auth_headers

ITEM = {"ticker": "PETR4", "quantity": 100, "avg_price": 30.0, "category": "auto"}


FII = {"HGLG11": "fiis"}


def _razao(*eventos) -> list[LedgerEntry]:
    lancamentos = []
    for indice, (kind, dia, quantidade, preco) in enumerate(eventos, start=1):
        lancamentos.append(
            LedgerEntry(
                kind=kind,
                symbol="HGLG11",
                traded_on=dia,
                quantity=quantidade,
                price=preco,
                id=indice,
            )
        )
    return lancamentos


C = TransactionKind.BUY
V = TransactionKind.SELL


def test_loss_is_available_to_offset_future_gains():
    apuracao = apurar(_razao((C, "2026-01-05", 100, 10.0), (V, "2026-02-10", 100, 8.0)), FII)
    fevereiro = apuracao.mes("2026-02", "fiis")

    assert fevereiro.result == -200
    assert fevereiro.ir_amount == 0
    assert "compensar ganho futuro" in fevereiro.observation
    assert apuracao.saldo_de_prejuizo["fiis"] == 200


def test_accumulated_loss_reduces_the_tax_due():
    sem_compensacao = apurar(
        _razao((C, "2026-01-05", 100, 10.0), (V, "2026-03-10", 100, 12.0)), FII
    )
    com_compensacao = apurar(
        _razao(
            (C, "2026-01-05", 200, 10.0),
            (V, "2026-02-10", 100, 8.5),
            (V, "2026-03-10", 100, 12.0),
        ),
        FII,
    )

    assert sem_compensacao.mes("2026-03", "fiis").ir_amount == pytest.approx(40.0)

    marco = com_compensacao.mes("2026-03", "fiis")
    assert marco.loss_offset_used == 150
    assert marco.taxable_profit == 50
    assert marco.ir_amount == pytest.approx(10.0)


def test_offset_never_exceeds_the_gain():
    apuracao = apurar(
        _razao(
            (C, "2026-01-05", 200, 10.0),
            (V, "2026-02-10", 100, 0.01),
            (V, "2026-03-10", 100, 11.0),
        ),
        FII,
    )
    marco = apuracao.mes("2026-03", "fiis")

    assert marco.loss_offset_used == 100
    assert marco.taxable_profit == 0
    assert marco.ir_amount == 0
    assert apuracao.saldo_de_prejuizo["fiis"] > 0, "o que sobrou do prejuízo continua disponível"


def test_exempt_month_preserves_the_loss_balance():
    apuracao = apurar(
        [
            LedgerEntry(
                kind=C, symbol="PETR4", traded_on="2026-01-05", quantity=3000, price=10.0, id=1
            ),
            LedgerEntry(
                kind=V, symbol="PETR4", traded_on="2026-02-10", quantity=2900, price=8.0, id=2
            ),
            LedgerEntry(
                kind=V, symbol="PETR4", traded_on="2026-03-10", quantity=100, price=12.0, id=3
            ),
        ],
        {"PETR4": "acoes_br"},
    )
    marco = apuracao.mes("2026-03", "acoes_br")

    assert marco.exempt is True
    assert marco.ir_amount == 0
    assert marco.loss_offset_used == 0
    assert apuracao.saldo_de_prejuizo["acoes_br"] == 5800


def test_tax_loss_balance_flows_through_the_api(client):
    headers = make_auth_headers("tax_offset_user")

    client.post(
        "/api/portfolio/position",
        headers=headers,
        json={"ticker": "HGLG11", "quantity": 100, "avg_price": 12.0, "category": "fiis"},
    )
    client.post(
        "/api/portfolio/sell",
        headers=headers,
        json={"ticker": "HGLG11", "quantity": 100, "sell_price": 10.0},
    )

    trades = client.get("/api/portfolio/trades", headers=headers).json()
    balances = {b["category"]: b for b in trades["tax_loss_balances"]}
    assert balances["fiis"]["available"] == 200.0
    assert trades["total_tax_loss_available"] == 200.0


def test_month_boundary_uses_brasilia_not_utc():
    late_night = datetime(2026, 3, 31, 22, 30, tzinfo=BRT)
    assert month_key(late_night.timestamp()) == "2026-03"

    assert late_night.astimezone(UTC).strftime("%Y-%m-%d") == "2026-04-01"


def test_month_start_is_the_first_day_in_brt():
    reference = datetime(2026, 3, 15, 12, 0, tzinfo=BRT).timestamp()
    start = datetime.fromtimestamp(month_start_timestamp(reference), tz=BRT)

    assert (start.year, start.month, start.day) == (2026, 3, 1)
    assert (start.hour, start.minute) == (0, 0)


def _dividend(**overrides) -> dict:
    today = datetime.now(BRT).date()
    body = {
        "ticker": "PETR4",
        "paid_at": today.isoformat(),
        "amount": 120.5,
        "kind": "dividendo",
    }
    body.update(overrides)
    return body


def test_dividends_crud_and_totals(client):
    headers = make_auth_headers("dividends_user")
    today = datetime.now(BRT).date()

    created = client.post("/api/dividends/received", headers=headers, json=_dividend())
    assert created.status_code == 201

    client.post(
        "/api/dividends/received",
        headers=headers,
        json=_dividend(
            ticker="HGLG11",
            amount=80.0,
            paid_at=(today - timedelta(days=40)).isoformat(),
        ),
    )

    body = client.get("/api/dividends/received", headers=headers).json()
    assert body["total_received"] == 200.5
    assert body["received_this_month"] == 120.5
    assert body["received_last_12m"] == 200.5
    assert len(body["by_month"]) == 2
    assert body["by_ticker"][0]["ticker"] == "PETR4"

    dividend_id = created.json()["id"]
    updated = client.put(
        f"/api/dividends/received/{dividend_id}", headers=headers, json={"amount": 200.0}
    )
    assert updated.json()["amount"] == 200.0
    assert updated.json()["ticker"] == "PETR4"

    assert (
        client.delete(f"/api/dividends/received/{dividend_id}", headers=headers).status_code == 200
    )
    assert client.get("/api/dividends/received", headers=headers).json()["total_received"] == 80.0


def test_dividends_compare_reality_with_the_estimate(client):
    headers = make_auth_headers("dividends_accuracy")
    client.post("/api/dividends/received", headers=headers, json=_dividend(amount=100.0))

    body = client.get(
        "/api/dividends/received", headers=headers, params={"estimated_monthly": 200.0}
    ).json()

    assert body["estimated_monthly"] == 200.0
    assert body["estimate_accuracy_pct"] == 50.0


def test_dividends_reach_the_dashboard(client):
    headers = make_auth_headers("dividends_dashboard")
    client.post("/api/dividends/received", headers=headers, json=_dividend(amount=333.0))

    summary = client.get("/api/dashboard", headers=headers).json()["summary"]
    assert summary["dividends_received_this_month"] == 333.0
    assert summary["dividends_received_last_12m"] == 333.0


def test_dividends_are_isolated_between_tenants(client):
    headers_a = make_auth_headers("div_tenant_a")
    headers_b = make_auth_headers("div_tenant_b")

    created = client.post("/api/dividends/received", headers=headers_a, json=_dividend()).json()

    assert client.get("/api/dividends/received", headers=headers_b).json()["items"] == []
    assert (
        client.put(
            f"/api/dividends/received/{created['id']}", headers=headers_b, json={"amount": 1.0}
        ).status_code
        == 404
    )
    assert (
        client.delete(f"/api/dividends/received/{created['id']}", headers=headers_b).status_code
        == 404
    )


def test_income_compare_puts_both_sides_on_the_same_screen(client):
    headers = make_auth_headers("income_compare_user")

    body = client.get(
        "/api/income-compare", headers=headers, params={"amount": 10_000, "horizon_months": 12}
    ).json()

    assert body["fixed_income"], "esperava opções de renda fixa"
    assert body["assets"], "esperava ativos pagadores de dividendo"
    assert body["verdict"]

    for option in body["fixed_income"] + body["assets"]:
        assert option["net_income_yield_pct"] >= 0
        assert option["income_basis"]
        assert option["monthly_income_estimate"] >= 0

    assert all(o["has_upside"] is False for o in body["fixed_income"])
    assert all(o["has_upside"] is True for o in body["assets"])


def test_income_compare_includes_the_users_own_fixed_income(client):
    headers = make_auth_headers("income_compare_own")
    client.post(
        "/api/fixed-income",
        headers=headers,
        json={
            "nome": "CDB do usuário",
            "tipo": "cdb",
            "valor_investido": 5000.0,
            "taxa": 14.0,
            "tipo_taxa": "pre_fixado",
            "data_aplicacao": "2025-06-01",
        },
    )

    body = client.get("/api/income-compare", headers=headers).json()
    assert any("CDB do usuário" in o["label"] for o in body["fixed_income"])


def test_income_compare_requires_auth(client):
    assert client.get("/api/income-compare").status_code == 401


def test_followed_suggestions_report_outcome_against_ibov(client):
    headers = make_auth_headers("followed_user")
    today = datetime.now(BRT).date()

    created = client.post(
        "/api/suggestions/followed",
        headers=headers,
        json={
            "ticker": "PETR4",
            "source": "opportunities",
            "quantity": 100,
            "price": 30.0,
            "followed_on": (today - timedelta(days=30)).isoformat(),
            "score_at_suggestion": 82.0,
            "verdict_at_suggestion": "STRONG_BUY",
        },
    )
    assert created.status_code == 201
    assert created.json()["invested"] == 3000.0

    body = client.get("/api/suggestions/followed", headers=headers).json()
    item = body["items"][0]

    assert item["current_value"] == 3800.0
    assert item["pnl"] == 800.0
    assert item["pnl_pct"] == pytest.approx(26.67, abs=0.01)
    assert item["days_held"] == 30
    assert item["score_at_suggestion"] == 82.0

    assert body["total_invested"] == 3000.0
    assert body["total_pnl"] == 800.0
    assert body["summary"]
    assert body["by_source"][0]["source"] == "Oportunidades"


def test_followed_suggestions_empty_state_explains_itself(client):
    headers = make_auth_headers("followed_empty")
    body = client.get("/api/suggestions/followed", headers=headers).json()

    assert body["items"] == []
    assert "auditar" in body["summary"]


def test_followed_suggestions_are_isolated_between_tenants(client):
    headers_a = make_auth_headers("followed_a")
    headers_b = make_auth_headers("followed_b")

    created = client.post(
        "/api/suggestions/followed",
        headers=headers_a,
        json={"ticker": "PETR4", "quantity": 10, "price": 30.0},
    ).json()

    assert client.get("/api/suggestions/followed", headers=headers_b).json()["items"] == []
    assert (
        client.delete(f"/api/suggestions/followed/{created['id']}", headers=headers_b).status_code
        == 404
    )


def test_data_quality_reports_coverage_per_field(client):
    headers = make_auth_headers("data_quality_user")
    body = client.get("/api/data-quality", headers=headers).json()

    assert body["scanned"] > 0
    fields = {f["field"]: f for f in body["fields"]}

    assert fields["price"]["coverage_pct"] == 100.0
    for field in body["fields"]:
        assert field["impact"]

    assert 0 < fields["avg_dividend"]["coverage_pct"] < 100


def test_data_quality_requires_auth(client):
    assert client.get("/api/data-quality").status_code == 401


def test_device_token_can_be_unregistered_on_logout(client):
    headers = make_auth_headers("push_user")

    client.post(
        "/api/notifications/register-token",
        headers=headers,
        json={"token": "token-de-teste-123456", "platform": "android"},
    )
    assert client.get("/api/preferences", headers=headers).json()["push_enabled"] is True

    resp = client.delete(
        "/api/notifications/register-token",
        headers=headers,
        params={"token": "token-de-teste-123456"},
    )
    assert resp.status_code == 204
    assert client.get("/api/preferences", headers=headers).json()["push_enabled"] is False


def test_preferences_report_whether_push_can_work(client):
    headers = make_auth_headers("push_status_user")
    prefs = client.get("/api/preferences", headers=headers).json()

    assert prefs["push_enabled"] is False
    assert prefs["registered_devices"] == 0


def test_alert_check_marks_triggered_like_the_job(client):
    headers = make_auth_headers("alert_check_user")

    created = client.post(
        "/api/alerts",
        headers=headers,
        json={"ticker": "PETR4", "condition": "above", "target_price": 10.0},
    ).json()

    triggered = client.get("/api/alerts/check", headers=headers).json()
    assert [t["id"] for t in triggered] == [created["id"]]

    alerts = client.get("/api/alerts", headers=headers).json()
    assert alerts[0]["triggered_at"] is not None

    assert client.get("/api/alerts/check", headers=headers).json() == []
