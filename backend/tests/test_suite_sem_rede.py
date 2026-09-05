from __future__ import annotations

import httpx
import pytest

from app.core import universe


def test_transporte_real_do_httpx_esta_bloqueado():
    with pytest.raises(RuntimeError, match="Chamada de rede na suíte"):
        httpx.get("https://brapi.dev/api/quote/list", timeout=1)


@pytest.mark.anyio
async def test_transporte_assincrono_tambem_esta_bloqueado(anyio_backend):
    async with httpx.AsyncClient(timeout=1) as cliente:
        with pytest.raises(RuntimeError, match="Chamada de rede na suíte"):
            await cliente.get("https://brapi.dev/api/quote/list")


def test_o_universo_vem_do_catalogo_fixo_e_nao_da_brapi():
    tipos = universe.get_type_map()

    assert tipos["PETR4"] == "stock"
    assert tipos["BOVA11"] == "etf"
    assert "IMAB11" not in tipos, (
        "o catálogo de teste imita a BRAPI real, que não lista ETF de renda fixa — "
        "é o buraco que KNOWN_ETFS existe para tapar"
    )


def test_o_testclient_continua_funcionando_apesar_do_bloqueio(client):
    assert client.get("/api/health").status_code == 200
