from __future__ import annotations

import pytest

from app.services.dividend_calendar_service import LOOKBACK_DAYS
from tests.conftest import make_auth_headers


@pytest.fixture()
def calendario(monkeypatch):
    from datetime import timedelta

    from app.core.brt import now_brt
    from app.repositories.asset_repository import AssetRepository

    hoje = now_brt().date()
    recente = (hoje - timedelta(days=30)).isoformat()
    antigo = (hoje - timedelta(days=LOOKBACK_DAYS + 60)).isoformat()

    async def _fake(symbol: str):
        if symbol.upper() != "PETR4":
            return []
        return [
            {"date": antigo, "value": 1.00},
            {"date": recente, "value": 0.50},
        ]

    monkeypatch.setattr(AssetRepository, "get_dividends", staticmethod(_fake))
    return {"recente": recente, "antigo": antigo}


class TestSugestao:
    def test_carteira_vazia_nao_sugere_nada(self, client, calendario):
        headers = make_auth_headers("u_div_vazia")

        corpo = client.get("/api/dividends/pending", headers=headers).json()

        assert corpo["items"] == []

    def test_sugere_o_provento_do_periodo_com_a_conta_a_vista(self, client, calendario):
        headers = make_auth_headers("u_div_sugere")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 200, "avg_price": 30.0},
            headers=headers,
        )

        corpo = client.get("/api/dividends/pending", headers=headers).json()

        assert corpo["count"] == 1
        item = corpo["items"][0]
        assert item["ticker"] == "PETR4"
        assert item["paid_at"] == calendario["recente"]
        assert item["rate_per_share"] == 0.50
        assert item["quantity_at_date"] == 200
        assert item["amount"] == 100.0

    def test_provento_antigo_demais_fica_de_fora(self, client, calendario):
        headers = make_auth_headers("u_div_antigo")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        datas = [
            i["paid_at"]
            for i in client.get("/api/dividends/pending", headers=headers).json()["items"]
        ]

        assert calendario["antigo"] not in datas

    def test_provento_ja_lancado_nao_reaparece(self, client, calendario):
        headers = make_auth_headers("u_div_ja_lancado")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )
        client.post(
            "/api/dividends/received",
            json={"ticker": "PETR4", "paid_at": calendario["recente"], "amount": 50.0},
            headers=headers,
        )

        assert client.get("/api/dividends/pending", headers=headers).json()["count"] == 0


class TestQuantidadeNaData:
    def test_a_quantidade_vem_da_projecao_do_razao(self, client, calendario):
        headers = make_auth_headers("u_div_razao")
        client.post(
            "/api/transactions",
            json={
                "kind": "buy",
                "symbol": "PETR4",
                "traded_on": "2020-01-10",
                "quantity": 100,
                "price": 20.0,
            },
            headers=headers,
        )
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 200, "avg_price": 25.0},
            headers=headers,
        )

        item = client.get("/api/dividends/pending", headers=headers).json()["items"][0]

        assert item["quantity_at_date"] == 100
        assert item["quantity_is_current"] is False
        assert item["amount"] == 50.0

    def test_sem_razao_usa_a_posicao_atual_e_avisa(self, client, calendario):
        headers = make_auth_headers("u_div_sem_razao")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 300, "avg_price": 30.0},
            headers=headers,
        )
        from app.storage import ledger_store

        ledger_store.delete_symbol_entries("PETR4", user_id="u_div_sem_razao")

        item = client.get("/api/dividends/pending", headers=headers).json()["items"][0]

        assert item["quantity_at_date"] == 300
        assert item["quantity_is_current"] is True
        assert any("posição de hoje" in c for c in item["caveats"])


@pytest.fixture()
def calendario_com_data_com(monkeypatch):
    from datetime import timedelta

    from app.core.brt import now_brt
    from app.repositories.asset_repository import AssetRepository

    hoje = now_brt().date()
    pagamento = (hoje - timedelta(days=30)).isoformat()
    data_com = (hoje - timedelta(days=45)).isoformat()

    async def _fake(symbol: str):
        if symbol.upper() != "PETR4":
            return []
        return [{"date": pagamento, "value": 0.50, "ex_date": data_com}]

    monkeypatch.setattr(AssetRepository, "get_dividends", staticmethod(_fake))
    return {"pagamento": pagamento, "data_com": data_com}


class TestDireito:
    def test_sem_data_com_na_fonte_o_direito_fica_indeterminado(self, client, calendario):
        headers = make_auth_headers("u_div_sem_datacom")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        item = client.get("/api/dividends/pending", headers=headers).json()["items"][0]

        assert item["entitlement"] == "indeterminado", (
            "sem a data-com nao ha como saber se a posicao ja existia quando o provento foi "
            "declarado, e afirmar que existia inventa dado"
        )
        assert any("data-com" in c for c in item["caveats"])

    def test_razao_anterior_a_data_com_prova_o_direito(self, client, calendario_com_data_com):
        headers = make_auth_headers("u_div_direito_provado")
        client.post(
            "/api/transactions",
            json={
                "kind": "buy",
                "symbol": "PETR4",
                "traded_on": "2020-01-10",
                "quantity": 100,
                "price": 20.0,
            },
            headers=headers,
        )
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 20.0},
            headers=headers,
        )

        item = client.get("/api/dividends/pending", headers=headers).json()["items"][0]

        assert item["entitlement"] == "provado", (
            "com data-com da fonte e lancamento anterior a ela, o direito e fato do razao, "
            "nao estimativa"
        )
        assert item["ex_date"] == calendario_com_data_com["data_com"]
        assert not any("data-com" in c for c in item["caveats"]), (
            "provado o direito, o aviso sobre a data-com so faria o usuario duvidar de um fato"
        )

    def test_compra_depois_da_data_com_nao_conta_quantidade(self, client, calendario_com_data_com):
        from datetime import date, timedelta

        depois = date.fromisoformat(calendario_com_data_com["data_com"]) + timedelta(days=3)
        headers = make_auth_headers("u_div_comprou_depois")
        client.post(
            "/api/transactions",
            json={
                "kind": "buy",
                "symbol": "PETR4",
                "traded_on": depois.isoformat(),
                "quantity": 100,
                "price": 20.0,
            },
            headers=headers,
        )

        corpo = client.get("/api/dividends/pending", headers=headers).json()

        assert corpo["count"] == 0, (
            "a base do provento e a posicao na data-com; quem comprou depois dela nao recebe, "
            "e sugerir o contrario creditaria dinheiro que nunca caiu"
        )

    def test_declaracao_posterior_devolve_o_direito_a_indeterminado(
        self, client, calendario_com_data_com
    ):
        headers = make_auth_headers("u_div_declarou_depois")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 20.0},
            headers=headers,
        )

        item = client.get("/api/dividends/pending", headers=headers).json()["items"][0]

        assert item["entitlement"] == "indeterminado", (
            "a declaracao de posicao absorve o que veio antes dela, entao o razao nao sabe "
            "dizer o que existia na data-com — e nao saber nao e provar"
        )
        assert item["quantity_is_current"] is True

    def test_a_quantidade_e_a_da_data_com_nao_a_do_pagamento(self, client, calendario_com_data_com):
        from datetime import date, timedelta

        entre = date.fromisoformat(calendario_com_data_com["data_com"]) + timedelta(days=5)
        headers = make_auth_headers("u_div_quantidade_datacom")
        client.post(
            "/api/transactions",
            json={
                "kind": "buy",
                "symbol": "PETR4",
                "traded_on": "2020-01-10",
                "quantity": 100,
                "price": 20.0,
            },
            headers=headers,
        )
        client.post(
            "/api/transactions",
            json={
                "kind": "buy",
                "symbol": "PETR4",
                "traded_on": entre.isoformat(),
                "quantity": 400,
                "price": 22.0,
            },
            headers=headers,
        )
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 500, "avg_price": 21.0},
            headers=headers,
        )

        item = client.get("/api/dividends/pending", headers=headers).json()["items"][0]

        assert item["quantity_at_date"] == 100, (
            "as 400 compradas entre a data-com e o pagamento nao dao direito a provento algum"
        )


class TestAvisos:
    def test_a_resposta_diz_que_nada_foi_lancado(self, client, calendario):
        headers = make_auth_headers("u_div_nota")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        nota = client.get("/api/dividends/pending", headers=headers).json()["note"]

        assert "Nada foi" in nota or "nada foi" in nota
        assert "extrato" in nota

    def test_jcp_avisa_que_o_valor_e_bruto(self, monkeypatch, client):
        from datetime import timedelta

        from app.core.brt import now_brt
        from app.repositories.asset_repository import AssetRepository

        recente = (now_brt().date() - timedelta(days=10)).isoformat()

        async def _fake(symbol: str):
            return [{"date": recente, "value": 1.0, "label": "JCP"}]

        monkeypatch.setattr(AssetRepository, "get_dividends", staticmethod(_fake))

        headers = make_auth_headers("u_div_jcp")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        item = client.get("/api/dividends/pending", headers=headers).json()["items"][0]

        assert item["kind"] == "jcp"
        assert any("bruto" in c for c in item["caveats"])


class TestConfirmacao:
    def test_nada_e_gravado_ate_confirmar(self, client, calendario):
        headers = make_auth_headers("u_div_nao_grava")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        client.get("/api/dividends/pending", headers=headers)

        assert client.get("/api/dividends/received", headers=headers).json()["items"] == []

    def test_confirmar_grava_so_o_que_foi_escolhido(self, client, calendario):
        headers = make_auth_headers("u_div_confirma")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )
        sugestoes = client.get("/api/dividends/pending", headers=headers).json()["items"]

        corpo = client.post(
            "/api/dividends/pending/confirm",
            json={
                "items": [
                    {
                        "ticker": sugestoes[0]["ticker"],
                        "paid_at": sugestoes[0]["paid_at"],
                        "amount": sugestoes[0]["amount"],
                        "kind": sugestoes[0]["kind"],
                    }
                ]
            },
            headers=headers,
        ).json()

        assert corpo["created"] == 1
        recebidos = client.get("/api/dividends/received", headers=headers).json()
        assert recebidos["total_received"] == sugestoes[0]["amount"]

    def test_o_confirmado_sai_da_lista_de_pendentes(self, client, calendario):
        headers = make_auth_headers("u_div_some")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )
        sugestao = client.get("/api/dividends/pending", headers=headers).json()["items"][0]
        client.post(
            "/api/dividends/pending/confirm",
            json={
                "items": [
                    {
                        "ticker": sugestao["ticker"],
                        "paid_at": sugestao["paid_at"],
                        "amount": sugestao["amount"],
                    }
                ]
            },
            headers=headers,
        )

        assert client.get("/api/dividends/pending", headers=headers).json()["count"] == 0

    def test_confirmar_lista_vazia_nao_e_erro(self, client):
        headers = make_auth_headers("u_div_vazio_confirm")

        resposta = client.post(
            "/api/dividends/pending/confirm", json={"items": []}, headers=headers
        )

        assert resposta.status_code == 200
        assert resposta.json()["created"] == 0

    def test_a_sugestao_de_um_nao_vaza_para_outro(self, client, calendario):
        dono = make_auth_headers("u_div_tenant_a")
        vizinho = make_auth_headers("u_div_tenant_b")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=dono,
        )

        assert client.get("/api/dividends/pending", headers=vizinho).json()["items"] == []


def test_falha_da_fonte_nao_derruba_a_lista(monkeypatch, client):
    from app.repositories.asset_repository import AssetRepository

    async def _explode(symbol: str):
        raise RuntimeError("fonte fora do ar")

    monkeypatch.setattr(AssetRepository, "get_dividends", staticmethod(_explode))

    headers = make_auth_headers("u_div_falha")
    client.post(
        "/api/portfolio/position",
        json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
        headers=headers,
    )

    resposta = client.get("/api/dividends/pending", headers=headers)

    assert resposta.status_code == 200
    assert resposta.json()["items"] == []
