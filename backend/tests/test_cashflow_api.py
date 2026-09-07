from __future__ import annotations

import pytest

from tests.conftest import make_auth_headers


@pytest.fixture
def headers(request) -> dict:
    return make_auth_headers(f"u_api_{request.node.name}"[:60])


def lancar(client, headers, **campos) -> dict:
    corpo = {"kind": "expense", "category": "mercado", "description": "Feira", "amount": 124.35}
    corpo.update(campos)
    resp = client.post("/api/cashflow/entries", json=corpo, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestOVocabularioEFechado:
    def test_a_rota_declara_as_tres_listas(self, client, headers):
        corpo = client.get("/api/cashflow/vocabulary", headers=headers).json()

        assert "moradia" in corpo["expense_categories"]
        assert "provento" in corpo["income_categories"]
        assert "rotativo_cartao" in corpo["debt_kinds"]

    def test_categoria_fora_do_vocabulario_da_422(self, client, headers):
        resp = client.post(
            "/api/cashflow/entries",
            json={
                "kind": "expense",
                "category": "cripto",
                "description": "x",
                "amount": 10,
                "due_on": "2026-09-10",
            },
            headers=headers,
        )

        assert resp.status_code == 422
        assert "vocabulário é fechado" in resp.text

    def test_valor_negativo_da_422(self, client, headers):
        resp = client.post(
            "/api/cashflow/entries",
            json={
                "kind": "expense",
                "category": "mercado",
                "description": "x",
                "amount": -10,
                "due_on": "2026-09-10",
            },
            headers=headers,
        )

        assert resp.status_code == 422

    def test_provento_lancado_pela_rota_da_422(self, client, headers):
        resp = client.post(
            "/api/cashflow/entries",
            json={
                "kind": "income",
                "category": "provento",
                "description": "PETR4",
                "amount": 340.0,
                "due_on": "2026-09-15",
            },
            headers=headers,
        )

        assert resp.status_code == 422
        assert "derivado do razão" in resp.text


class TestOMesPelaRota:
    def test_fato_e_projecao_saem_separados(self, client, headers):
        lancar(
            client,
            headers,
            kind="income",
            category="salario",
            description="Salário",
            amount=6418.73,
            due_on="2026-09-05",
            paid_on="2026-09-05",
        )
        lancar(
            client,
            headers,
            category="moradia",
            description="Aluguel",
            amount=2150.00,
            due_on="2026-09-05",
            paid_on="2026-09-05",
        )
        lancar(
            client,
            headers,
            category="contas_da_casa",
            description="Energia",
            amount=187.44,
            due_on="2026-09-22",
        )

        corpo = client.get("/api/cashflow/month?month=2026-09", headers=headers).json()

        assert corpo["received"] == 6418.73
        assert corpo["paid"] == 2150.00
        assert corpo["committed"] == 187.44
        assert corpo["free_now"] == 4081.29
        assert corpo["has_range"] is False, "sem mês fechado não há estimativa"
        assert corpo["surplus_low"] == corpo["free_now"], (
            "ausência de estimativa não vira zero otimista"
        )
        assert [d["description"] for d in corpo["due"]] == ["Energia"]

    def test_marcar_paga_move_do_comprometido_para_o_pago(self, client, headers):
        criada = lancar(
            client, headers, category="contas_da_casa", amount=187.44, due_on="2026-09-22"
        )

        resp = client.post(
            f"/api/cashflow/entries/{criada['id']}/paid",
            json={"paid_on": "2026-09-22"},
            headers=headers,
        )
        assert resp.status_code == 204

        corpo = client.get("/api/cashflow/month?month=2026-09", headers=headers).json()
        assert corpo["committed"] == 0.0
        assert corpo["paid"] == 187.44
        assert corpo["due"] == []


class TestADividaPelaRota:
    def test_sem_taxa_nao_ha_classe(self, client, headers):
        resp = client.post(
            "/api/cashflow/debts",
            json={
                "kind": "rotativo_cartao",
                "description": "Rotativo do cartão",
                "balance": 890.0,
            },
            headers=headers,
        )

        assert resp.status_code == 201, resp.text
        corpo = resp.json()
        assert corpo["class"] == "no_rate"
        assert corpo["flip_rate"] is None, (
            "o produto não estima taxa de rotativo, e sem taxa não há veredito a derrubar"
        )

    def test_tipo_de_divida_fora_do_vocabulario_da_422(self, client, headers):
        resp = client.post(
            "/api/cashflow/debts",
            json={"kind": "agiota", "description": "x", "balance": 100.0},
            headers=headers,
        )

        assert resp.status_code == 422
        assert "vocabulário é fechado" in resp.text

    def test_quitar_tira_a_divida_da_lista(self, client, headers):
        criada = client.post(
            "/api/cashflow/debts",
            json={"kind": "cheque_especial", "description": "Especial", "balance": 1200.0},
            headers=headers,
        ).json()

        client.post(f"/api/cashflow/debts/{criada['id']}/settled", headers=headers)

        assert client.get("/api/cashflow/debts", headers=headers).json() == []


class TestAPonteRespondeSemPerguntar:
    def test_a_sobra_traz_o_mes_e_a_ordem(self, client, headers):
        lancar(
            client,
            headers,
            kind="income",
            category="salario",
            description="Salário",
            amount=6418.73,
            due_on="2026-09-05",
            paid_on="2026-09-05",
        )

        corpo = client.get("/api/surplus?month=2026-09", headers=headers).json()

        assert corpo["month"]["free_now"] == 6418.73
        assert corpo["has_cash"] is True
        assert [p["type"] for p in corpo["cascade"]["steps"]] == ["contribution"]
        assert corpo["cascade"]["available_to_invest"] == 6418.73

    def test_sem_caixa_lancado_a_rota_diz_que_nao_ha(self, client, headers):
        corpo = client.get("/api/surplus?month=2026-09", headers=headers).json()

        assert corpo["has_cash"] is False, (
            "é o que faz a tela pedir o valor E dizer por que está pedindo, em vez de abrir vazia"
        )
        assert corpo["cascade"]["steps"] == []

    def test_lancamento_de_outro_titular_nao_vaza(self, client, headers):
        lancar(
            client,
            headers,
            kind="income",
            category="salario",
            description="Salário",
            amount=6418.73,
            due_on="2026-09-05",
            paid_on="2026-09-05",
        )

        vizinho = make_auth_headers("u_api_vizinho")
        corpo = client.get("/api/cashflow/month?month=2026-09", headers=vizinho).json()

        assert corpo["received"] == 0.0
