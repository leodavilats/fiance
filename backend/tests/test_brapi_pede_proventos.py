import httpx
import pytest

from app.collectors import universal
from app.core import cache


class _RespostaFalsa:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


@pytest.fixture()
def chamadas(monkeypatch):
    registro = []

    def _get(url, params=None, timeout=None):
        registro.append({"url": url, "params": params or {}})
        return _RespostaFalsa(
            {
                "results": [
                    {
                        "symbol": "PETR4",
                        "regularMarketPrice": 40.0,
                        "dividendsData": {
                            "cashDividends": [
                                {"paymentDate": "2026-03-10", "rate": 1.5},
                                {"paymentDate": "2026-06-10", "rate": 1.5},
                            ]
                        },
                    }
                ]
            }
        )

    monkeypatch.setattr(httpx, "get", _get)
    monkeypatch.setattr(cache, "get", lambda *a, **k: None)
    monkeypatch.setattr(cache, "set", lambda *a, **k: None)
    monkeypatch.setattr(universal.cache, "get", lambda *a, **k: None)
    monkeypatch.setattr(universal.cache, "set", lambda *a, **k: None)
    return registro


class TestOProventoEPedido:
    def test_a_chamada_pede_dividends(self, chamadas):
        universal._brapi_raw("PETR4")

        assert chamadas, "nenhuma chamada foi feita"
        assert chamadas[0]["params"].get("dividends") == "true", (
            "sem dividends=true a BRAPI não devolve dividendsData, e o DY de toda a "
            "carteira vira zero em silêncio"
        )

    def test_sem_o_parametro_a_lista_de_proventos_viria_vazia(self, chamadas):
        universal._brapi_raw("PETR4")
        payload = chamadas[0]["params"]

        assert set(payload) >= {"token", "fundamental", "dividends", "range", "interval"}
