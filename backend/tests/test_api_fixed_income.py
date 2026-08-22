"""Renda fixa como entidade de primeira classe (D1, D2, D9)."""

from datetime import UTC, date, datetime, timedelta

from tests.conftest import make_auth_headers


def _hoje() -> date:
    return datetime.now(UTC).date()


def _cdb(**overrides) -> dict:
    body = {
        "nome": "CDB Banco X",
        "tipo": "cdb",
        "valor_investido": 40000.0,
        "taxa": 13.0,
        "tipo_taxa": "pre_fixado",
        "data_aplicacao": (_hoje() - timedelta(days=365)).isoformat(),
        "vencimento": (_hoje() + timedelta(days=365)).isoformat(),
        "liquidez": "no_vencimento",
    }
    body.update(overrides)
    return body


def test_crud_round_trip(client):
    headers = make_auth_headers("fi_crud")

    assert client.get("/api/fixed-income", headers=headers).json()["items"] == []

    created = client.post("/api/fixed-income", headers=headers, json=_cdb())
    assert created.status_code == 201
    position = created.json()
    assert position["nome"] == "CDB Banco X"
    assert position["taxa"] == 13.0

    listing = client.get("/api/fixed-income", headers=headers).json()
    assert len(listing["items"]) == 1

    updated = client.put(
        f"/api/fixed-income/{position['id']}",
        headers=headers,
        json={"taxa": 14.5},
    )
    assert updated.status_code == 200
    assert updated.json()["taxa"] == 14.5
    assert updated.json()["nome"] == "CDB Banco X"

    assert client.delete(f"/api/fixed-income/{position['id']}", headers=headers).status_code == 200
    assert client.get("/api/fixed-income", headers=headers).json()["items"] == []


def test_position_is_marked_to_market_not_frozen(client):
    """ "Coloquei R$ 40 mil em CDB e o app diz que rendi zero"."""
    headers = make_auth_headers("fi_mark")

    position = client.post("/api/fixed-income", headers=headers, json=_cdb()).json()

    assert position["valor_atual"] > position["valor_investido"]
    assert position["rendimento_acumulado"] > 0
    assert position["rendimento_pct"] > 0
    assert position["yield_equivalente_pct"] > 0
    assert position["meses_decorridos"] > 11


def test_details_survive_a_new_client(client):
    """ "Troquei de navegador e minha renda fixa virou R$ 0 de rendimento"."""
    headers = make_auth_headers("fi_persist")

    client.post(
        "/api/fixed-income",
        headers=headers,
        json=_cdb(tipo_taxa="pos_fixado", percentual_cdi=110.0),
    )

    reread = client.get("/api/fixed-income", headers=headers).json()["items"][0]
    assert reread["percentual_cdi"] == 110.0
    assert reread["taxa"] == 13.0
    assert reread["data_aplicacao"] == _cdb()["data_aplicacao"]
    assert reread["rendimento_acumulado"] > 0


def test_maturity_projection_and_upcoming_alert(client):
    headers = make_auth_headers("fi_maturity")

    longe = client.post("/api/fixed-income", headers=headers, json=_cdb()).json()
    assert longe["valor_no_vencimento"] > longe["valor_atual"]
    assert longe["vencimento_proximo"] is False

    perto = client.post(
        "/api/fixed-income",
        headers=headers,
        json=_cdb(
            nome="CDB vencendo",
            vencimento=(_hoje() + timedelta(days=12)).isoformat(),
        ),
    ).json()
    assert perto["vencimento_proximo"] is True
    assert perto["dias_para_vencimento"] == 12


def test_hidden_position_is_kept_but_excluded_from_totals(client):
    headers = make_auth_headers("fi_hidden")

    visivel = client.post("/api/fixed-income", headers=headers, json=_cdb()).json()
    oculto = client.post(
        "/api/fixed-income", headers=headers, json=_cdb(nome="Reserva", oculto=True)
    ).json()

    listing = client.get("/api/fixed-income", headers=headers).json()
    assert len(listing["items"]) == 2
    assert listing["total_investido"] == visivel["valor_investido"]
    assert oculto["oculto"] is True


def test_fixed_income_reaches_the_dashboard_totals(client):
    """O patrimônio total e a renda passiva paravam de contar a renda fixa."""
    headers = make_auth_headers("fi_dashboard")

    before = client.get("/api/dashboard", headers=headers).json()["summary"]

    client.post("/api/fixed-income", headers=headers, json=_cdb())

    after = client.get("/api/dashboard", headers=headers).json()["summary"]

    assert after["total_invested"] == before["total_invested"] + 40000.0
    assert after["total_current"] > after["total_invested"]
    assert after["total_pnl"] > before["total_pnl"]
    assert after["yearly_dividends_estimate"] > before["yearly_dividends_estimate"]


def test_fixed_income_position_is_not_typed_as_a_stock(client):
    """Posições RF apareciam com asset_type = br_stock no mobile."""
    headers = make_auth_headers("fi_asset_type")
    client.post("/api/fixed-income", headers=headers, json=_cdb())

    positions = client.get("/api/dashboard", headers=headers).json()["positions"]
    rf = [p for p in positions if p["category_resolved"] == "renda_fixa"]
    assert rf, "renda fixa deveria aparecer entre as posições"
    assert rf[0]["asset_type"] == "renda_fixa"
    assert rf[0]["current_price"] != rf[0]["avg_price"]


def test_fixed_income_is_isolated_between_tenants(client):
    headers_a = make_auth_headers("fi_tenant_a")
    headers_b = make_auth_headers("fi_tenant_b")

    created = client.post("/api/fixed-income", headers=headers_a, json=_cdb()).json()

    assert client.get("/api/fixed-income", headers=headers_b).json()["items"] == []
    assert (
        client.put(
            f"/api/fixed-income/{created['id']}", headers=headers_b, json={"taxa": 99.0}
        ).status_code
        == 404
    )
    assert client.delete(f"/api/fixed-income/{created['id']}", headers=headers_b).status_code == 404

    still_there = client.get("/api/fixed-income", headers=headers_a).json()["items"][0]
    assert still_there["taxa"] == 13.0


def test_rejects_maturity_before_application(client):
    headers = make_auth_headers("fi_bad_dates")
    resp = client.post(
        "/api/fixed-income",
        headers=headers,
        json=_cdb(
            data_aplicacao=_hoje().isoformat(),
            vencimento=(_hoje() - timedelta(days=1)).isoformat(),
        ),
    )
    assert resp.status_code == 422


def test_endpoints_require_auth(client):
    assert client.get("/api/fixed-income").status_code == 401
    assert client.post("/api/fixed-income", json=_cdb()).status_code == 401
    assert client.put("/api/fixed-income/1", json={"taxa": 1.0}).status_code == 401
    assert client.delete("/api/fixed-income/1").status_code == 401
