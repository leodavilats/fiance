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


class TestAvisos:
    def test_toda_sugestao_avisa_sobre_a_data_com(self, client, calendario):
        headers = make_auth_headers("u_div_datacom")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        item = client.get("/api/dividends/pending", headers=headers).json()["items"][0]

        assert any("data-com" in c for c in item["caveats"])

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
