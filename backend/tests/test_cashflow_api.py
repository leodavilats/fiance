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

    def test_com_meta_declarada_o_aporte_nao_diz_que_nao_ha_meta(self, client, headers):
        """A razão do passo de aporte vinha fixa: `/surplus` nunca consultava as metas.

        Quem declarou alocação-alvo lia "Sem meta de alocação declarada" no único passo da
        ordem — o produto contradizendo o que a pessoa acabara de salvar duas telas antes.
        """
        client.put(
            "/api/goals",
            json={
                "goals": [
                    {"category": "acoes_br", "target_pct": 60.0},
                    {"category": "fiis", "target_pct": 40.0},
                ]
            },
            headers=headers,
        )
        lancar(
            client,
            headers,
            kind="income",
            category="salario",
            description="Salário",
            amount=3000.0,
            due_on="2026-09-05",
            paid_on="2026-09-05",
        )

        corpo = client.get("/api/surplus?month=2026-09", headers=headers).json()
        aporte = next(p for p in corpo["cascade"]["steps"] if p["type"] == "contribution")

        assert "Sem meta" not in aporte["reason"]
        assert aporte["reference"] == "meta"

    def test_sem_meta_declarada_o_aporte_diz_que_a_ordem_sai_por_score(self, client, headers):
        lancar(
            client,
            headers,
            kind="income",
            category="salario",
            description="Salário",
            amount=3000.0,
            due_on="2026-09-05",
            paid_on="2026-09-05",
        )

        corpo = client.get("/api/surplus?month=2026-09", headers=headers).json()
        aporte = next(p for p in corpo["cascade"]["steps"] if p["type"] == "contribution")

        assert "Sem meta" in aporte["reason"], (
            "o padrão do produto não é objetivo da pessoa, e a tela precisa dizer isso"
        )
        assert aporte["reference"] == "score"

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


class TestEditarUmLancamento:
    def test_o_valor_errado_se_corrige_sem_apagar_e_relancar(self, client, headers):
        criado = lancar(
            client,
            headers,
            category="moradia",
            description="Aluguel",
            amount=2150.00,
            due_on="2026-09-05",
            paid_on="2026-09-05",
        )

        resp = client.put(
            f"/api/cashflow/entries/{criado['id']}",
            json={
                "kind": "expense",
                "category": "moradia",
                "description": "Aluguel",
                "amount": 2250.00,
                "due_on": "2026-09-05",
                "paid_on": "2026-09-05",
            },
            headers=headers,
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["amount"] == 2250.00
        assert resp.json()["id"] == criado["id"], "editar não cria um segundo lançamento"

        mes = client.get("/api/cashflow/month?month=2026-09", headers=headers).json()
        assert mes["paid"] == 2250.00

    def test_editar_move_o_lancamento_de_mes(self, client, headers):
        criado = lancar(
            client,
            headers,
            category="mercado",
            description="Feira",
            amount=124.35,
            due_on="2026-08-31",
            paid_on="2026-08-31",
        )

        client.put(
            f"/api/cashflow/entries/{criado['id']}",
            json={
                "kind": "expense",
                "category": "mercado",
                "description": "Feira",
                "amount": 124.35,
                "due_on": "2026-09-01",
                "paid_on": "2026-09-01",
            },
            headers=headers,
        )

        assert client.get("/api/cashflow/month?month=2026-08", headers=headers).json()["paid"] == 0
        assert (
            client.get("/api/cashflow/month?month=2026-09", headers=headers).json()["paid"]
            == 124.35
        )

    def test_editar_para_categoria_fora_do_vocabulario_da_422(self, client, headers):
        criado = lancar(client, headers, due_on="2026-09-10")

        resp = client.put(
            f"/api/cashflow/entries/{criado['id']}",
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

    def test_editar_lancamento_de_outro_titular_da_404(self, client, headers):
        criado = lancar(client, headers, due_on="2026-09-10")
        vizinho = make_auth_headers("u_api_editar_vizinho")

        resp = client.put(
            f"/api/cashflow/entries/{criado['id']}",
            json={
                "kind": "expense",
                "category": "mercado",
                "description": "x",
                "amount": 10,
                "due_on": "2026-09-10",
            },
            headers=vizinho,
        )

        assert resp.status_code == 404


class TestOMesAnteriorComoMolde:
    def semear_agosto(self, client, headers) -> None:
        lancar(
            client,
            headers,
            kind="income",
            category="salario",
            description="Salário",
            amount=6418.73,
            due_on="2026-08-05",
            paid_on="2026-08-05",
        )
        lancar(
            client,
            headers,
            category="moradia",
            description="Aluguel",
            amount=2150.00,
            due_on="2026-08-05",
            paid_on="2026-08-05",
        )
        lancar(
            client,
            headers,
            category="mercado",
            description="Feira",
            amount=804.15,
            due_on="2026-08-14",
            paid_on="2026-08-14",
        )

    def test_a_origem_e_o_mes_anterior_quando_nao_se_diz_qual(self, client, headers):
        self.semear_agosto(client, headers)

        corpo = client.get("/api/cashflow/month/template?target=2026-09", headers=headers).json()

        assert corpo["source"] == "2026-08"
        assert corpo["target"] == "2026-09"

    def test_o_molde_marca_o_que_repete_e_ja_traz_a_data_no_destino(self, client, headers):
        self.semear_agosto(client, headers)

        corpo = client.get("/api/cashflow/month/template?target=2026-09", headers=headers).json()
        por_categoria = {c["category"]: c for c in corpo["candidates"]}

        assert por_categoria["moradia"]["repeats"] is True
        assert por_categoria["moradia"]["due_on"] == "2026-09-05"
        assert por_categoria["mercado"]["repeats"] is False

    def test_o_molde_nao_grava_nada(self, client, headers):
        self.semear_agosto(client, headers)
        client.get("/api/cashflow/month/template?target=2026-09", headers=headers)

        mes = client.get("/api/cashflow/month?month=2026-09", headers=headers).json()
        assert mes["paid"] == 0.0, "ler o molde é leitura; gravar é o lote, e ele é outra rota"

    def test_janeiro_busca_dezembro_do_ano_anterior(self, client, headers):
        corpo = client.get("/api/cashflow/month/template?target=2027-01", headers=headers).json()

        assert corpo["source"] == "2026-12"

    def test_um_mes_nao_e_molde_de_si_mesmo(self, client, headers):
        resp = client.get(
            "/api/cashflow/month/template?target=2026-09&source=2026-09", headers=headers
        )

        assert resp.status_code == 422
        assert "molde de si mesmo" in resp.text


class TestOLoteGravaTudoOuNada:
    def test_o_lote_cria_os_lancamentos_do_mes_novo(self, client, headers):
        resp = client.post(
            "/api/cashflow/entries/batch",
            json={
                "entries": [
                    {
                        "kind": "income",
                        "category": "salario",
                        "description": "Salário",
                        "amount": 6418.73,
                        "due_on": "2026-09-05",
                        "paid_on": "2026-09-05",
                    },
                    {
                        "kind": "expense",
                        "category": "moradia",
                        "description": "Aluguel",
                        "amount": 2150.00,
                        "due_on": "2026-09-05",
                    },
                ]
            },
            headers=headers,
        )

        assert resp.status_code == 201, resp.text
        assert [e["id"] for e in resp.json()] == sorted(e["id"] for e in resp.json())

        mes = client.get("/api/cashflow/month?month=2026-09", headers=headers).json()
        assert mes["received"] == 6418.73
        assert mes["committed"] == 2150.00, "o copiado nasce a vencer, não pago"

    def test_um_lancamento_invalido_derruba_o_lote_inteiro(self, client, headers):
        resp = client.post(
            "/api/cashflow/entries/batch",
            json={
                "entries": [
                    {
                        "kind": "expense",
                        "category": "moradia",
                        "description": "Aluguel",
                        "amount": 2150.00,
                        "due_on": "2026-09-05",
                    },
                    {
                        "kind": "expense",
                        "category": "cripto",
                        "description": "x",
                        "amount": 10,
                        "due_on": "2026-09-05",
                    },
                ]
            },
            headers=headers,
        )

        assert resp.status_code == 422
        mes = client.get("/api/cashflow/month?month=2026-09", headers=headers).json()
        assert mes["committed"] == 0.0, (
            "meio molde de mês é pior que molde nenhum: a pessoa não teria como saber o que "
            "entrou e o que ficou de fora"
        )

    def test_lote_vazio_e_recusado(self, client, headers):
        resp = client.post("/api/cashflow/entries/batch", json={"entries": []}, headers=headers)

        assert resp.status_code == 422
