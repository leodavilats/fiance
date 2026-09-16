from __future__ import annotations

import pytest

from tests.conftest import make_auth_headers


@pytest.fixture()
def razao(client, request):
    headers = make_auth_headers(f"u_razao_{request.node.name}")
    lancamentos = [
        {"kind": "buy", "symbol": "PETR4", "traded_on": "2024-01-10", "quantity": 100, "price": 30},
        {"kind": "buy", "symbol": "ITSA4", "traded_on": "2025-03-05", "quantity": 200, "price": 10},
        {"kind": "sell", "symbol": "PETR4", "traded_on": "2025-06-20", "quantity": 50, "price": 40},
        {"kind": "buy", "symbol": "PETR4", "traded_on": "2026-02-01", "quantity": 30, "price": 35},
    ]
    for corpo in lancamentos:
        client.post("/api/transactions", json=corpo, headers=headers)
    return headers


def _datas(corpo: dict) -> list[str]:
    return [i["traded_on"] for i in corpo["items"]]


class TestFiltroDeTipo:
    def test_um_tipo_traz_so_aquele_tipo(self, client, razao):
        corpo = client.get("/api/transactions?kind=sell", headers=razao).json()

        assert [i["kind"] for i in corpo["items"]] == ["sell"]

    def test_tipos_repetidos_somam(self, client, razao):
        corpo = client.get("/api/transactions?kind=buy&kind=sell", headers=razao).json()

        assert corpo["count"] == 4, "repetir o parametro soma tipos, nao troca o filtro"

    def test_tipo_invalido_recusa_em_vez_de_ignorar(self, client, razao):
        resposta = client.get("/api/transactions?kind=inventado", headers=razao)

        assert resposta.status_code == 422, (
            "filtro que o servidor ignora em silencio devolve lista errada parecendo certa"
        )


class TestFiltroDePeriodo:
    def test_faixa_fechada_corta_os_dois_lados(self, client, razao):
        corpo = client.get(
            "/api/transactions?traded_from=2025-01-01&traded_to=2025-12-31", headers=razao
        ).json()

        assert sorted(_datas(corpo)) == ["2025-03-05", "2025-06-20"]

    def test_a_faixa_inclui_os_extremos(self, client, razao):
        corpo = client.get(
            "/api/transactions?traded_from=2025-06-20&traded_to=2025-06-20", headers=razao
        ).json()

        assert _datas(corpo) == ["2025-06-20"], "faixa de um dia so precisa trazer aquele dia"

    def test_periodo_e_tipo_se_acumulam(self, client, razao):
        corpo = client.get(
            "/api/transactions?kind=buy&traded_from=2025-01-01", headers=razao
        ).json()

        assert sorted(_datas(corpo)) == ["2025-03-05", "2026-02-01"]


class TestPaginacao:
    def test_o_cursor_continua_de_onde_parou_sem_repetir(self, client, razao):
        primeira = client.get("/api/transactions?limit=2", headers=razao).json()
        segunda = client.get(
            f"/api/transactions?limit=2&cursor={primeira['next_cursor']}", headers=razao
        ).json()

        assert primeira["has_more"] is True
        assert set(_datas(primeira)).isdisjoint(_datas(segunda)), (
            "cursor keyset que repete linha faz o usuario contar o mesmo lancamento duas vezes"
        )
        assert len(_datas(primeira)) + len(_datas(segunda)) == 4

    def test_o_filtro_sobrevive_a_pagina_seguinte(self, client, razao):
        primeira = client.get("/api/transactions?kind=buy&limit=1", headers=razao).json()
        segunda = client.get(
            f"/api/transactions?kind=buy&limit=1&cursor={primeira['next_cursor']}",
            headers=razao,
        ).json()

        assert [i["kind"] for i in segunda["items"]] == ["buy"], (
            "filtro perdido na segunda pagina traz de volta o que o usuario acabou de excluir"
        )
