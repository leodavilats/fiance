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
    """Nulo não é erro: é "use a minha sobra"."""
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
    """O serviço caía num 50/25/25 fixo, que nada na carteira da pessoa sustentava."""
    headers = make_auth_headers("test_quick_invest_sem_meta")

    resp = client.post("/api/quick-invest", headers=headers, json={"cash_available": 1000.0})
    assert resp.status_code == 200

    body = resp.json()
    assert body["basis"] == "score", (
        "sem alocação-alvo declarada não se inventa divisão por categoria"
    )
    assert "score" in body["summary"].lower()


def test_todo_dinheiro_tem_destino_ou_motivo(client):
    """O que sobra vem com o porquê.

    Era o defeito relatado: com R$ 1.000 a sugestão trazia um ativo só e o resto ficava sem
    destino, sem uma linha dizendo por que. Três causas, e todas silenciosas — a fatia de renda
    fixa descartada por não haver título na lista de oportunidades, a fatia de 10% do terceiro
    ativo caindo abaixo da ordem mínima, e o troco de cota inteira.
    """
    headers = make_auth_headers("test_quick_invest_destino")

    resp = client.post("/api/quick-invest", headers=headers, json={"cash_available": 1000.0})
    assert resp.status_code == 200

    body = resp.json()
    alocado = body["allocated_cash"]
    restante = body["remaining_cash"]

    # `allocated_cash` é anulado fora do nível prescritivo: ele instrui uma compra.
    if alocado is not None:
        assert abs(alocado + restante - body["total_cash"]) < 0.01, "a conta tem de fechar"

    if restante > 0.01:
        assert body["unallocated"], (
            f"R$ {restante:.2f} sem destino e nenhuma linha dizendo por que — "
            "`remaining_cash` sozinho é um número sem explicação"
        )
        assert all(u["reason"] for u in body["unallocated"])
        assert all(u["value"] is not None for u in body["unallocated"]), (
            "o valor sem destino é análise, não instrução: sobrevive em todo nível"
        )


def test_renda_fixa_nao_desaparece_da_sugestao(client):
    """A fatia de renda fixa sumia porque só se olhava a lista de oportunidades.

    Ela tem ações, FIIs, BDRs e ETFs, e nunca um título. Com meta de renda fixa, o dinheiro
    evaporava sem uma linha na tela.
    """
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

    # `amount` instrui uma compra, então é anulado fora do nível prescritivo -- e o que sustenta
    # a fatia (a razão e a referência) fica. É a mesma regra do valor por ativo.
    nivel = body["affirmation"]["level"]
    if nivel >= 3:
        assert fatia["amount"] > 0
    else:
        assert fatia["amount"] is None
    assert "compare" in fatia["rationale"].lower(), (
        "o produto não tem catálogo de títulos: ele diz quanto vai para a categoria e manda "
        "comparar, em vez de nomear uma oferta que não conhece"
    )
