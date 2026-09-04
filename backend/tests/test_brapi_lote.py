from __future__ import annotations

import time

import pytest

from app.collectors import circuit, universal
from app.core import cache

pytestmark = pytest.mark.real_cache


@pytest.fixture(autouse=True)
def cache_limpo(tmp_path, monkeypatch):
    from app.core import cache_backends

    monkeypatch.setattr(cache_backends, "DB_PATH", tmp_path / "lote.db")
    cache.reset_connection()
    circuit.reset()
    yield
    cache.reset_connection()


class _RespostaFalsa:
    def __init__(self, results: list[dict]) -> None:
        self._results = results

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"results": self._results}


@pytest.fixture()
def brapi(monkeypatch):
    chamadas: list[str] = []
    conhecidos = {"PETR4", "VALE3", "ITUB4", "BBAS3", "WEGE3"}

    def _get(url, params=None, timeout=None):
        pedidos = url.rsplit("/", 1)[-1].split(",")
        chamadas.append(url)
        return _RespostaFalsa(
            [{"symbol": t, "regularMarketPrice": 10.0} for t in pedidos if t in conhecidos]
        )

    monkeypatch.setattr(universal.httpx, "get", _get)
    return chamadas


class TestOLoteEconomizaPedidos:
    def test_um_pedido_cobre_o_lote_inteiro(self, brapi):
        pedidos = universal.prefetch_brapi_raw(["PETR4", "VALE3", "ITUB4"])

        assert pedidos == 1
        assert len(brapi) == 1

    def test_cada_ticker_fica_acessivel_sozinho_depois(self, brapi):
        universal.prefetch_brapi_raw(["PETR4", "VALE3"])
        brapi.clear()

        assert universal._brapi_raw("PETR4")["regularMarketPrice"] == 10.0
        assert universal._brapi_raw("VALE3")["regularMarketPrice"] == 10.0
        assert brapi == []

    def test_o_universo_e_quebrado_em_lotes(self, brapi, monkeypatch):
        monkeypatch.setattr(universal, "_BRAPI_LOTE", 20)
        universo = [f"AAA{i}" for i in range(45)]

        pedidos = universal.prefetch_brapi_raw(universo)

        assert pedidos == 3

    def test_o_que_ja_esta_em_cache_nao_entra_no_lote(self, brapi):
        universal.prefetch_brapi_raw(["PETR4"])
        brapi.clear()

        universal.prefetch_brapi_raw(["PETR4", "VALE3"])

        assert brapi[0].endswith("/VALE3")

    def test_nada_faltando_nao_gera_pedido(self, brapi):
        universal.prefetch_brapi_raw(["PETR4"])
        brapi.clear()

        assert universal.prefetch_brapi_raw(["PETR4"]) == 0
        assert brapi == []


class TestAAusenciaEhLembrada:
    def test_ticker_que_a_fonte_nao_conhece_nao_e_repedido(self, brapi):
        universal.prefetch_brapi_raw(["PETR4", "FANTASMA9"])
        brapi.clear()

        assert universal._brapi_raw("FANTASMA9") == {}
        assert brapi == [], "ausência conhecida não deveria voltar à rede"

    def test_a_ausencia_expira_antes_do_dado_bom(self):
        assert universal._AUSENTE_TTL < universal._BRAPI_RAW_TTL

    def test_ausencia_nao_se_confunde_com_dado(self, brapi):
        universal.prefetch_brapi_raw(["FANTASMA9"])

        assert universal._ler_raw("FANTASMA9") == {}
        assert universal._ler_raw("NUNCA_PEDIDO") is None


class TestFalhaNaoViraAusencia:
    def test_lote_que_falha_nao_carimba_ticker_como_inexistente(self, monkeypatch):
        def _explode(url, params=None, timeout=None):
            raise RuntimeError("fonte fora do ar")

        monkeypatch.setattr(universal.httpx, "get", _explode)

        universal.prefetch_brapi_raw(["PETR4", "VALE3"])

        assert universal._ler_raw("PETR4") is None
        assert universal._ler_raw("VALE3") is None

    def test_lote_que_falha_interrompe_os_seguintes(self, monkeypatch):
        chamadas = []

        def _explode(url, params=None, timeout=None):
            chamadas.append(url)
            raise RuntimeError("fonte fora do ar")

        monkeypatch.setattr(universal.httpx, "get", _explode)
        monkeypatch.setattr(universal, "_BRAPI_LOTE", 2)

        universal.prefetch_brapi_raw(["A1", "A2", "A3", "A4", "A5", "A6"])

        assert len(chamadas) == 1, "insistir com a fonte caída gasta cota à toa"

    def test_disjuntor_aberto_nem_tenta(self, monkeypatch):
        chamadas = []
        monkeypatch.setattr(universal.httpx, "get", lambda *a, **k: chamadas.append(1))
        monkeypatch.setattr(circuit, "allows", lambda _: False)

        assert universal.prefetch_brapi_raw(["PETR4"]) == 0
        assert chamadas == []


class TestOCaminhoAvulsoContinuaValendo:
    def test_ticker_fora_do_lote_ainda_e_buscado_sozinho(self, brapi):
        assert universal._brapi_raw("PETR4")["regularMarketPrice"] == 10.0
        assert len(brapi) == 1

    def test_o_avulso_tambem_lembra_a_ausencia(self, brapi):
        assert universal._brapi_raw("FANTASMA9") == {}
        brapi.clear()

        assert universal._brapi_raw("FANTASMA9") == {}
        assert brapi == []

    def test_o_vencimento_do_dado_bom_e_o_de_sempre(self, brapi):
        universal.prefetch_brapi_raw(["PETR4"])

        _, idade = cache.get_with_age("brapi_raw:PETR4")

        assert idade == 0
        bruto = cache.backend().get_raw("brapi_raw:PETR4")
        assert bruto[1] == pytest.approx(time.time() + universal._BRAPI_RAW_TTL, abs=5)


class TestOAquecimentoNaoPenduraORequest:
    def test_com_outro_aquecendo_seguimos_em_vez_de_esperar(self, brapi, monkeypatch):
        monkeypatch.setattr(universal, "_PREFETCH_ESPERA", 0.05)
        universal._prefetch_lock.acquire()
        try:
            comeco = time.monotonic()
            pedidos = universal.prefetch_brapi_raw(["PETR4"])
            demora = time.monotonic() - comeco
        finally:
            universal._prefetch_lock.release()

        assert pedidos == 1, "o aquecimento precisa acontecer mesmo sem a vez"
        assert demora < 1.0, f"esperou {demora:.2f}s pela vez de outro"

    def test_o_lock_e_devolvido_mesmo_quando_a_fonte_estoura(self, monkeypatch):
        def _explode(url, params=None, timeout=None):
            raise RuntimeError("fonte fora do ar")

        monkeypatch.setattr(universal.httpx, "get", _explode)
        universal.prefetch_brapi_raw(["PETR4"])

        assert universal._prefetch_lock.acquire(timeout=0.1), "lock vazou"
        universal._prefetch_lock.release()
