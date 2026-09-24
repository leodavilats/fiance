from tests.conftest import make_auth_headers


def _campo(client, headers, campo: str) -> dict[str, float | None]:
    resp = client.get(
        "/api/opportunities",
        headers=headers,
        params={"include_held": "true", "page_size": 50},
    )
    assert resp.status_code == 200
    return {o["ticker"]: o[campo] for o in resp.json()["items"]}


def test_a_meta_de_renda_muda_o_preco_teto_e_nao_o_preco_justo(client):
    headers = make_auth_headers("prefs_effect_user")

    client.put("/api/preferences", headers=headers, json={"desired_yield_stock": 0.06})
    teto_modesto = _campo(client, headers, "personal_ceiling")
    justo_modesto = _campo(client, headers, "fair_price")

    client.put("/api/preferences", headers=headers, json={"desired_yield_stock": 0.12})
    teto_exigente = _campo(client, headers, "personal_ceiling")
    justo_exigente = _campo(client, headers, "fair_price")

    shared = [t for t in teto_modesto if teto_modesto[t] and teto_exigente.get(t)]
    assert shared, "esperava pelo menos um ativo com preço-teto calculado"

    assert all(teto_exigente[t] < teto_modesto[t] for t in shared)
    assert justo_modesto == justo_exigente, (
        "o yield da pessoa é meta de renda, não valor da empresa: ele entrava na borda da "
        "faixa e trocava o veredito de quem só mudou a própria meta"
    )


def test_two_users_with_different_prefs_get_different_ceilings(client):
    headers_a = make_auth_headers("calc_leak_a")
    headers_b = make_auth_headers("calc_leak_b")

    client.put("/api/preferences", headers=headers_a, json={"desired_yield_stock": 0.05})
    client.put("/api/preferences", headers=headers_b, json={"desired_yield_stock": 0.15})

    from_a = _campo(client, headers_a, "personal_ceiling")
    from_b = _campo(client, headers_b, "personal_ceiling")

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
    headers = make_auth_headers("provenance_user")
    resp = client.get("/api/opportunities", headers=headers, params={"include_held": "true"})
    items = resp.json()["items"]
    assert items

    for field in ("confidence", "data_years", "consensus_methods", "trend_basis"):
        assert field in items[0]

    petr = next((o for o in items if o["ticker"] == "PETR4"), None)
    assert petr is not None
    assert petr["data_years"] > 0
    assert petr["confidence"] > 0
