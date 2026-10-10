from __future__ import annotations

import httpx
import pytest

from datajob.rede import ESPERAS, Ausente, Indisponivel, baixar

URL = "https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A2026.ZIP"


def _respostas(*sequencia):
    pedidos = []

    def get(url, **_):
        pedidos.append(url)
        item = sequencia[len(pedidos) - 1]
        if isinstance(item, Exception):
            raise item
        return httpx.Response(item, content=b"zip")

    return get, pedidos


def test_queda_no_meio_do_download_tenta_de_novo():
    get, pedidos = _respostas(httpx.RemoteProtocolError("conexão caiu"), 200)
    esperas = []

    assert baixar(URL, get=get, dormir=esperas.append) == b"zip"
    assert len(pedidos) == 2, "o anual de 2026 caiu assim na carga de produção em 2026-10-10"
    assert esperas == [ESPERAS[0]]


def test_arquivo_inexistente_nao_e_tentado_de_novo():
    get, pedidos = _respostas(404)

    with pytest.raises(Ausente):
        baixar(URL, get=get, dormir=lambda _: None)
    assert len(pedidos) == 1


def test_desiste_depois_de_todas_as_tentativas():
    get, pedidos = _respostas(*[503] * (len(ESPERAS) + 1))

    with pytest.raises(Indisponivel, match="503"):
        baixar(URL, get=get, dormir=lambda _: None)
    assert len(pedidos) == len(ESPERAS) + 1


def test_pagina_html_com_status_200_tenta_de_novo():
    pedidos = []

    def get(url, **_):
        pedidos.append(url)
        if len(pedidos) == 1:
            return httpx.Response(
                200,
                content=b"<html>Requisicao invalida!</html>",
                headers={"content-type": "text/html"},
            )
        return httpx.Response(200, content=b"[]", headers={"content-type": "application/json"})

    assert baixar(URL, get=get, dormir=lambda _: None) == b"[]"
    assert len(pedidos) == 2, "o BCB devolve essa página de vez em quando, com status 200"
