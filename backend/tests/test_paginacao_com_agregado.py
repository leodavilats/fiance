from __future__ import annotations

from contextlib import contextmanager
from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import event

from app.core.brt import now_brt
from app.core.database import engine
from app.services.fixed_income_service import FixedIncomeService
from app.storage import portfolio_store
from tests.conftest import make_auth_headers


def _espiar(monkeypatch, alvo, nome):
    chamadas: list[dict] = []
    original = getattr(alvo, nome)

    def _espiao(*args, **kwargs):
        chamadas.append(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(alvo, nome, _espiao)
    return chamadas


@contextmanager
def _consultas(tabela: str):
    capturadas: list[str] = []

    def _ouvir(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT") and f"FROM {tabela}" in statement:
            capturadas.append(" ".join(statement.split()))

    event.listen(engine, "before_cursor_execute", _ouvir)
    try:
        yield capturadas
    finally:
        event.remove(engine, "before_cursor_execute", _ouvir)


def _folhear(client, url, headers, limite):
    paginas = []
    cursor = None
    for _ in range(50):
        sufixo = f"&cursor={cursor}" if cursor else ""
        resposta = client.get(f"{url}?limit={limite}{sufixo}", headers=headers)
        assert resposta.status_code == 200, resposta.text
        corpo = resposta.json()
        paginas.append(corpo)
        if not corpo["has_more"]:
            return paginas
        cursor = corpo["next_cursor"]
    raise AssertionError("a paginação não terminou: o cursor não avança")


def _agregado(corpo):
    return {k: v for k, v in corpo.items() if k not in ("items", "next_cursor", "has_more")}


def _conferir_paginas(client, url, headers, limite):
    paginas = _folhear(client, url, headers, limite)
    inteira = client.get(f"{url}?limit=500", headers=headers).json()

    assert len(paginas) > 1, "o cenário precisa de mais de uma página"
    assert len(paginas[0]["items"]) == limite, "a página traz o limite pedido, nem mais nem menos"
    ids = [item["id"] for pagina in paginas for item in pagina["items"]]
    assert len(ids) == len(set(ids)), "nenhum item pode aparecer em duas páginas"
    assert ids == [item["id"] for item in inteira["items"]], (
        "folhear com cursor devolve o mesmo conjunto, na mesma ordem, que a lista inteira"
    )
    for pagina in paginas:
        assert _agregado(pagina) == _agregado(inteira), (
            "o total é da conta: não pode encolher nem mudar conforme a rolagem"
        )
    return paginas, inteira


class TestProventos:
    def _semear(self, client, headers):
        hoje = now_brt().date()
        lancamentos = [
            (0, "PETR4", "10.10"),
            (0, "VALE3", "0.07"),
            (40, "PETR4", "20.20"),
            (100, "VALE3", "33.33"),
            (200, "PETR4", "5.05"),
            (400, "VALE3", "100.00"),
            (401, "PETR4", "1.11"),
        ]
        for dias, ticker, valor in lancamentos:
            resposta = client.post(
                "/api/dividends/received",
                headers=headers,
                json={
                    "ticker": ticker,
                    "paid_at": (hoje - timedelta(days=dias)).isoformat(),
                    "amount": float(valor),
                },
            )
            assert resposta.status_code == 201, resposta.text
        return hoje, lancamentos

    def test_a_consulta_da_pagina_leva_o_limite(self, client, monkeypatch):
        headers = make_auth_headers("u_pag_agr_proventos_sql")
        self._semear(client, headers)
        chamadas = _espiar(monkeypatch, portfolio_store, "list_dividends_received")

        client.get("/api/dividends/received?limit=3", headers=headers)

        assert chamadas and all(c.get("limit") is not None for c in chamadas), (
            "a consulta da página tem de levar o limite: sem ele o banco devolve tudo e o "
            "corte acontece só no payload"
        )

    def test_o_agregado_nao_carrega_a_linha_inteira(self, client):
        headers = make_auth_headers("u_pag_agr_proventos_colunas")
        self._semear(client, headers)

        with _consultas("dividends_received") as consultas:
            client.get("/api/dividends/received?limit=3", headers=headers)

        inteiras = [c for c in consultas if "dividends_received.note" in c]
        leves = [c for c in consultas if "dividends_received.note" not in c]
        assert len(inteiras) == 1 and "LIMIT" in inteiras[0], (
            f"só a página lê a linha inteira, e com limite: {consultas}"
        )
        assert leves, "o agregado sai de uma consulta própria"
        for consulta in leves:
            assert "dividends_received.kind" not in consulta, (
                f"o agregado lê só data, ticker e valor: {consulta}"
            )
            assert "dividends_received.user_id =" in consulta, "toda consulta filtra por titular"

    def test_o_total_e_da_conta_em_toda_pagina(self, client):
        headers = make_auth_headers("u_pag_agr_proventos")
        hoje, lancamentos = self._semear(client, headers)

        _, inteira = _conferir_paginas(client, "/api/dividends/received", headers, 3)

        corte = (hoje - timedelta(days=365)).isoformat()
        doze = [v for d, _, v in lancamentos if (hoje - timedelta(days=d)).isoformat() >= corte]
        assert inteira["total_count"] == 7
        assert inteira["total_received"] == float(sum(Decimal(v) for *_, v in lancamentos))
        assert inteira["received_this_month"] == 10.17
        assert inteira["received_last_12m"] == float(sum(Decimal(v) for v in doze))
        assert inteira["monthly_average_12m"] == 17.19
        assert [(t["ticker"], t["total"], t["count"]) for t in inteira["by_ticker"]] == [
            ("VALE3", 133.40, 3),
            ("PETR4", 36.46, 4),
        ]
        assert sum(m["count"] for m in inteira["by_month"]) == 7
        assert inteira["by_month"][0]["month"] == hoje.strftime("%Y-%m")
        assert inteira["by_month"][0]["total"] == 10.17

    def test_o_agregado_nao_ve_outra_conta(self, client):
        dono = make_auth_headers("u_pag_agr_proventos_dono")
        self._semear(client, dono)
        outro = make_auth_headers("u_pag_agr_proventos_outro")

        corpo = client.get("/api/dividends/received?limit=2", headers=outro).json()

        assert corpo["items"] == []
        assert corpo["total_count"] == 0
        assert corpo["total_received"] == 0.0
        assert corpo["by_ticker"] == [], "o agregado filtra por titular, como a página"


class TestRendaFixa:
    def _semear(self, client, headers):
        hoje = now_brt().date()
        for indice in range(5):
            resposta = client.post(
                "/api/fixed-income",
                headers=headers,
                json={
                    "nome": f"CDB {indice}",
                    "tipo": "cdb",
                    "valor_investido": 1000.0 * (indice + 1) + 0.33,
                    "taxa": 12.0 + indice,
                    "tipo_taxa": "pre_fixado",
                    "data_aplicacao": (hoje - timedelta(days=30 * (indice + 1))).isoformat(),
                    "vencimento": (hoje + timedelta(days=365)).isoformat(),
                    "liquidez": "no_vencimento",
                    "oculto": indice == 4,
                },
            )
            assert resposta.status_code == 201, resposta.text

    def test_a_marcacao_completa_so_roda_para_a_pagina(self, client, monkeypatch):
        headers = make_auth_headers("u_pag_agr_rf_sql")
        self._semear(client, headers)
        chamadas = _espiar(monkeypatch, portfolio_store, "list_fixed_income")
        marcadas = _espiar(monkeypatch, FixedIncomeService, "_mark_to_market")

        primeira = client.get("/api/fixed-income?limit=2", headers=headers).json()

        assert len(primeira["items"]) == 2
        assert len(marcadas) == 2, (
            "a posição inteira (vencimento, equivalências) só se calcula para a linha exibida; "
            "o total usa só o valor atual de cada uma"
        )
        assert chamadas and all(c.get("limit") is not None for c in chamadas), (
            "a página vem do banco com limite"
        )

    def test_o_agregado_nao_carrega_a_linha_inteira(self, client):
        headers = make_auth_headers("u_pag_agr_rf_colunas")
        self._semear(client, headers)

        with _consultas("fixed_income_positions") as consultas:
            client.get("/api/fixed-income?limit=2", headers=headers)

        inteiras = [c for c in consultas if "fixed_income_positions.nome" in c]
        leves = [c for c in consultas if "fixed_income_positions.nome" not in c]
        assert len(inteiras) == 1 and "LIMIT" in inteiras[0], (
            f"só a página lê a linha inteira, e com limite: {consultas}"
        )
        assert any("count(" in c.lower() for c in leves), "a contagem é contagem, não lista"
        for consulta in leves:
            assert "fixed_income_positions.created_at" not in consulta, (
                f"o agregado lê só as colunas da marcação: {consulta}"
            )
            assert "fixed_income_positions.user_id =" in consulta, (
                "toda consulta filtra por titular"
            )

    def test_o_total_e_da_conta_em_toda_pagina(self, client):
        headers = make_auth_headers("u_pag_agr_rf")
        self._semear(client, headers)

        paginas, inteira = _conferir_paginas(client, "/api/fixed-income", headers, 2)
        visiveis = [i for p in paginas for i in p["items"] if not i["oculto"]]

        assert inteira["total_count"] == 5, "a contagem inclui a posição oculta"
        assert inteira["total_investido"] == 10001.32, "a oculta não entra na soma"
        assert inteira["total_atual"] == pytest.approx(
            sum(i["valor_atual"] for i in visiveis), abs=0.005
        ), "o total bate com a soma das linhas que a tela mostra"
        assert inteira["total_rendimento"] == pytest.approx(
            inteira["total_atual"] - inteira["total_investido"], abs=0.005
        )

    def test_o_agregado_nao_ve_outra_conta(self, client):
        self._semear(client, make_auth_headers("u_pag_agr_rf_dono"))
        outro = make_auth_headers("u_pag_agr_rf_outro")

        corpo = client.get("/api/fixed-income?limit=2", headers=outro).json()

        assert corpo["items"] == []
        assert corpo["total_count"] == 0
        assert corpo["total_investido"] == 0.0, "o agregado filtra por titular, como a página"
