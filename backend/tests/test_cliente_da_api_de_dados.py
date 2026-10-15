from __future__ import annotations

import httpx
import pytest

from app.collectors import mercado


def _retrato(codigo: str) -> dict:
    return {
        "ativo": {"codigo": codigo, "tipo": "stock", "cnpj": "1"},
        "irmaos": [{"codigo": codigo, "classe": "ON", "preco": 10.0, "volume_medio": 1.0}],
        "demonstracoes": [
            {
                "tipo": "DFP", "data_referencia": "2025-12-31", "versao": 1,
                "data_entrega": "2026-03-01", "fim_exercicio": "2025-12-31", "receita": 100.0,
                "lucro_controladores": 10.0, "patrimonio_controladores": 50.0, "divida_bruta": None,
            },
            {
                "tipo": "ITR", "data_referencia": "2026-06-30", "versao": 1,
                "data_entrega": "2026-08-01", "fim_exercicio": "2026-06-30", "receita": 60.0,
                "lucro_controladores": 6.0, "patrimonio_controladores": None, "divida_bruta": None,
            },
        ],
    }  # fmt: skip


@pytest.fixture
def api(monkeypatch):
    pedidos: list[httpx.Request] = []

    def responder(pedido: httpx.Request) -> httpx.Response:
        pedidos.append(pedido)
        rota = pedido.url.path
        if rota == "/v1/retratos":
            codigos = pedido.url.params["codigos"].split(",")
            return httpx.Response(200, json={"dados": {c: _retrato(c) for c in codigos}})
        if rota == "/v1/ativos":
            if pedido.url.params.get("cursor") is None:
                return httpx.Response(
                    200, json={"dados": [{"codigo": "AAAA3", "tipo": "stock"}], "proximo": "AAAA3"}
                )
            return httpx.Response(
                200, json={"dados": [{"codigo": "BBBB3", "tipo": "fii"}], "proximo": None}
            )
        if rota.startswith("/v1/ativos/XPTO3"):
            return httpx.Response(404, json={"erro": "Ativo XPTO3 não encontrado na base."})
        if rota == "/v1/ativos/PETR4/proventos":
            return httpx.Response(200, json={"dados": [
                {"data_com": "2026-03-01", "data_pagamento": "2026-03-20", "valor": 1.0,
                 "tipo": "DIVIDENDO", "origem": "b3_historico", "estimado": False}
            ], "proximo": None})  # fmt: skip
        return httpx.Response(500)

    cliente = httpx.Client(
        base_url="http://dados", transport=httpx.MockTransport(responder),
        headers={"Authorization": "Bearer fd_teste"},
    )  # fmt: skip
    monkeypatch.setattr(mercado, "_cliente", cliente)
    return pedidos


def test_retratos_saem_em_lotes_de_cinquenta_e_viram_o_pacote_do_snapshot(api):
    codigos = [f"T{i:03d}3" for i in range(120)]

    pacotes = mercado.ler_pacotes(codigos)

    assert len(api) == 3, "120 tickers em três chamadas, não em 120"
    pacote = pacotes["T0003"]
    assert [r["data_referencia"] for r in pacote["resultados"]] == ["2025-12-31", "2026-06-30"]
    assert [b["data_referencia"] for b in pacote["balancos"]] == ["2025-12-31"], (
        "documento sem patrimônio não vira balanço"
    )
    assert api[0].headers["Authorization"] == "Bearer fd_teste"


def test_lista_percorre_todas_as_paginas(api):
    assert [a["codigo"] for a in mercado.ler_lista()] == ["AAAA3", "BBBB3"]


def test_ticker_desconhecido_e_ausencia_e_nao_falha(api):
    assert mercado.ler_proventos("XPTO3") == []
    assert mercado.ler_historico("XPTO3", 30) == {}


def test_proventos_chegam_no_formato_do_app(api):
    assert mercado.ler_proventos("PETR4") == [
        {"data_com": "2026-03-01", "data_pagamento": "2026-03-20", "valor": 1.0}
    ]


def test_sem_url_ou_chave_a_ausencia_e_declarada(monkeypatch):
    monkeypatch.setattr(mercado, "_cliente", None)
    monkeypatch.setattr(
        mercado,
        "get_settings",
        lambda: type("S", (), {"dados_api_url": "", "dados_api_chave": ""})(),
    )

    with pytest.raises(mercado.SemBaseDeMercado):
        mercado.cliente()
