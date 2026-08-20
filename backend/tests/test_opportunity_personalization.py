"""D5 — o cache de oportunidades era global mas o cálculo é personalizado.

`_SCAN_CACHE_KEY` era uma chave única e o valor cacheado já vinha com o
`desired_yield` e o `risk_profile` de quem aqueceu o cache: as metas de yield da
tela de Configurações não tinham efeito, e o usuário B recebia preço justo e
score calculados com as preferências do usuário A.
"""

from tests.conftest import make_auth_headers


def _fair_prices(client, headers) -> dict[str, float | None]:
    resp = client.get(
        "/api/opportunities",
        headers=headers,
        params={"include_held": "true", "page_size": 50},
    )
    assert resp.status_code == 200
    return {o["ticker"]: o["fair_price"] for o in resp.json()["items"]}


def test_desired_yield_changes_the_fair_price_the_user_sees(client):
    headers = make_auth_headers("prefs_effect_user")

    client.put("/api/preferences", headers=headers, json={"desired_yield_stock": 0.06})
    conservative = _fair_prices(client, headers)

    client.put("/api/preferences", headers=headers, json={"desired_yield_stock": 0.12})
    demanding = _fair_prices(client, headers)

    shared = [t for t in conservative if conservative[t] and demanding.get(t)]
    assert shared, "esperava pelo menos um ativo com preço justo calculado"

    # Exigir o dobro de yield derruba o preço teto do Bazin — logo o consenso.
    assert any(demanding[t] < conservative[t] for t in shared)


def test_two_users_with_different_prefs_get_different_fair_prices(client):
    headers_a = make_auth_headers("calc_leak_a")
    headers_b = make_auth_headers("calc_leak_b")

    client.put("/api/preferences", headers=headers_a, json={"desired_yield_stock": 0.05})
    client.put("/api/preferences", headers=headers_b, json={"desired_yield_stock": 0.15})

    # A aquece o cache primeiro — antes, isso fixava o cálculo de A para B.
    from_a = _fair_prices(client, headers_a)
    from_b = _fair_prices(client, headers_b)

    shared = [t for t in from_a if from_a[t] and from_b.get(t)]
    assert shared
    assert any(from_a[t] != from_b[t] for t in shared)


def test_risk_profile_changes_the_score(client):
    headers = make_auth_headers("risk_profile_user")

    def scores() -> dict[str, float]:
        resp = client.get(
            "/api/opportunities",
            headers=headers,
            params={"include_held": "true", "page_size": 50},
        )
        return {o["ticker"]: o["score"] for o in resp.json()["items"]}

    client.put("/api/preferences", headers=headers, json={"risk_profile": "conservative"})
    conservative = scores()

    client.put("/api/preferences", headers=headers, json={"risk_profile": "aggressive"})
    aggressive = scores()

    assert conservative and aggressive
    assert any(conservative[t] != aggressive.get(t) for t in conservative)


def test_opportunity_carries_its_own_provenance(client):
    """confidence/data_years/consensus_methods eram calculados e descartados."""
    headers = make_auth_headers("provenance_user")
    resp = client.get("/api/opportunities", headers=headers, params={"include_held": "true"})
    items = resp.json()["items"]
    assert items

    for field in ("confidence", "data_years", "consensus_methods", "trend_basis"):
        assert field in items[0]

    petr = next((o for o in items if o["ticker"] == "PETR4"), None)
    assert petr is not None
    # PETR4 tem histórico de dividendos e série de preços no stub.
    assert petr["data_years"] > 0
    assert petr["confidence"] > 0
