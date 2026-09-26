from tests.conftest import make_auth_headers


def test_quick_invest_with_valid_cash_returns_allocations(client):
    uid = "test_quick_invest_valid"
    headers = make_auth_headers(uid)

    resp = client.post(
        "/api/quick-invest",
        headers=headers,
        json={"cash_available": 10000.0},
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["total_cash"] == 10000.0
    assert "allocations" in body
    assert "remaining_cash" in body
    assert "allocated_cash" in body
    assert isinstance(body["allocations"], list)


def test_quick_invest_with_zero_cash_is_rejected(client):
    uid = "test_quick_invest_zero"
    headers = make_auth_headers(uid)

    resp = client.post(
        "/api/quick-invest",
        headers=headers,
        json={"cash_available": 0},
    )
    assert resp.status_code == 422


def test_quick_invest_with_negative_cash_is_rejected(client):
    uid = "test_quick_invest_negative"
    headers = make_auth_headers(uid)

    resp = client.post(
        "/api/quick-invest",
        headers=headers,
        json={"cash_available": -100.0},
    )
    assert resp.status_code == 422


def test_quick_invest_requires_auth(client):
    resp = client.post("/api/quick-invest", json={"cash_available": 1000.0})
    assert resp.status_code == 401


def test_valor_nulo_resolve_da_cascata(client):
    headers = make_auth_headers("test_quick_invest_cascata")

    resp = client.post("/api/quick-invest", headers=headers, json={})
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert body["cash_source"] == "cascade", (
        "sem valor informado, quem decide quanto há para aportar é a cascata do caixa — "
        "e não o cliente"
    )


def test_valor_informado_diz_que_foi_informado(client):
    headers = make_auth_headers("test_quick_invest_informado")

    resp = client.post("/api/quick-invest", headers=headers, json={"cash_available": 1000.0})
    assert resp.status_code == 200

    body = resp.json()
    assert body["cash_source"] == "informed"
    assert body["total_cash"] == 1000.0


def test_sem_meta_declarada_a_base_e_score_e_nao_uma_divisao_inventada(client):
    headers = make_auth_headers("test_quick_invest_sem_meta")

    resp = client.post("/api/quick-invest", headers=headers, json={"cash_available": 1000.0})
    assert resp.status_code == 200

    body = resp.json()
    assert body["basis"] == "score", (
        "sem alocação-alvo declarada não se inventa divisão por categoria"
    )
    assert "score" in body["summary"].lower()


def test_todo_dinheiro_tem_destino_ou_motivo(client, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "affirmation_level", 3, raising=False)
    headers = make_auth_headers("test_quick_invest_destino")

    resp = client.post("/api/quick-invest", headers=headers, json={"cash_available": 1000.0})
    assert resp.status_code == 200

    body = resp.json()
    alocado = body["allocated_cash"]
    restante = body["remaining_cash"]

    assert abs(alocado + restante - body["total_cash"]) < 0.01, "a conta tem de fechar"

    if restante > 0.01:
        assert body["unallocated"], (
            f"R$ {restante:.2f} sem destino e nenhuma linha dizendo por que — "
            "`remaining_cash` sozinho é um número sem explicação"
        )
        assert all(u["reason"] for u in body["unallocated"])
        assert abs(sum(u["value"] for u in body["unallocated"]) - restante) < 0.01, (
            "cada real que não foi alocado está numa linha com motivo"
        )


def test_fora_do_prescritivo_o_que_sobra_vem_so_com_o_motivo(client):
    headers = make_auth_headers("test_quick_invest_motivo")

    resp = client.post("/api/quick-invest", headers=headers, json={"cash_available": 1000.0})
    assert resp.status_code == 200

    body = resp.json()
    assert body["remaining_cash"] is None, (
        "caixa menos o que sobra é o valor alocado: a sobra sai junto com ele"
    )
    assert body["unallocated"], "o cenário precisa de sobra para provar alguma coisa"
    assert all(u["reason"] and u["value"] is None for u in body["unallocated"]), (
        "o motivo é análise e fica; o valor sem destino, somado, dá o alocado por subtração"
    )


def test_renda_fixa_nao_desaparece_da_sugestao(client):
    uid = "test_quick_invest_rf"
    headers = make_auth_headers(uid)

    client.put(
        "/api/goals",
        headers=headers,
        json={"goals": [{"category": "renda_fixa", "target_pct": 100.0}]},
    )

    resp = client.post("/api/quick-invest", headers=headers, json={"cash_available": 1000.0})
    assert resp.status_code == 200

    body = resp.json()
    if body["basis"] != "goals":
        return

    fatia = body["fixed_income"]
    assert fatia is not None, "a meta pedia renda fixa e a fatia não veio"
    assert fatia["reference_source"], "a taxa de referência precisa dizer de onde veio"

    nivel = body["affirmation"]["level"]
    if nivel >= 3:
        assert fatia["amount"] > 0
    else:
        assert fatia["amount"] is None
    assert "compare" in fatia["rationale"].lower(), (
        "o produto não tem catálogo de títulos: ele diz quanto vai para a categoria e manda "
        "comparar, em vez de nomear uma oferta que não conhece"
    )


def test_a_margem_chega_em_fracao_e_a_razao_a_le_assim():
    from app.models import AssetType, Opportunity
    from app.services.quick_invest_service import QuickInvestService

    opp = Opportunity(
        ticker="PETR4",
        asset_type=AssetType.br_stock,
        verdict="STRONG_BUY",
        label="Bem abaixo do preço justo",
        margin_of_safety=0.34,
    )

    razao = QuickInvestService()._porque(opp, "acoes_br", {})

    assert "margem de 34%" in razao, (
        "a margem é fração: comparada com 20, a razão nunca aparecia, e formatada sem ×100 "
        "sairia como 0%"
    )
