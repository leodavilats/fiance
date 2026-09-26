from __future__ import annotations

import asyncio
import re
from datetime import UTC, datetime

import pytest

import app.core.cache as cache_mod
import app.core.cache_backends as backends_mod
from app.analysis.fair_price import (
    MAX_GROWTH,
    RATE_BASE_AVERAGE,
    ValuationRates,
    compute_fair_price,
    rates_for_valuation,
)
from app.collectors import rates, universal
from app.core import universe

REF = datetime(2026, 9, 23, tzinfo=UTC)

TAXAS = ValuationRates(
    discount_rate=0.145, fii_yield=0.095, rate_base=RATE_BASE_AVERAGE, selic_pct=9.5
)


def _anos(valores: list[float], inicio: int = 2021) -> list[dict]:
    return [{"date": f"{inicio + i}-06-01", "value": v} for i, v in enumerate(valores)]


def _acao(**kw):
    base = {
        "price": 10.0,
        "eps": 1.0,
        "book_value": 8.0,
        "dividends": _anos([0.5] * 5),
        "asset_type": "br_stock",
        "net_income_history": [120.0, 120.0, 120.0],
        "equity_history": [800.0, 800.0, 800.0],
        "net_income_ttm": 120.0,
        "rates": TAXAS,
        "reference": REF,
    }
    base.update(kw)
    return compute_fair_price(**base)


def _fii(**kw):
    base = {
        "price": 100.0,
        "eps": None,
        "book_value": 100.0,
        "dividends": _anos([9.5] * 5),
        "asset_type": "fii",
        "rates": TAXAS,
        "reference": REF,
    }
    base.update(kw)
    return compute_fair_price(**base)


def _principal(r) -> dict:
    return next(m for m in r.methods if m["role"] == "principal")


@pytest.fixture
def cache_real(tmp_path, monkeypatch):
    monkeypatch.setattr(backends_mod, "DB_PATH", tmp_path / "cache.db")
    cache_mod.set_backend(backends_mod.SqliteBackend())
    yield
    cache_mod.set_backend(None)


@pytest.mark.real_cache
class TestCacheVencidoSobrevive:
    def test_a_taxa_vencida_e_servida_quando_o_bcb_cai(self, cache_real, monkeypatch):
        cache_mod.set(
            rates._CACHE_KEY, {"cdi_anual": 10.0, "selic_anual": 10.0, "source": "bcb"}, -120
        )
        monkeypatch.setattr(rates.circuit, "allows", lambda provider: False)

        assert rates.get_rates()["source"] == rates.SOURCE_CACHE_VENCIDO, (
            "a leitura que confere validade não pode apagar o vencido: sem ele, o BCB fora do ar "
            "cai direto na estimativa, e juro estimado não avalia — todo preço justo some"
        )

    def test_provento_vencido_e_servido_quando_a_fonte_falha(self, cache_real, monkeypatch):
        vencido = _anos([1.0] * 5)
        cache_mod.set("udiv:PETR4", vencido, -120)
        monkeypatch.setattr(universal, "_dividends_sync", lambda symbol: None)

        assert asyncio.run(universal.fetch_dividends("PETR4")) == vencido

    def test_sem_cache_a_falha_se_declara(self, cache_real, monkeypatch):
        monkeypatch.setattr(universal, "_dividends_sync", lambda symbol: None)

        assert asyncio.run(universal.fetch_dividends("PETR4")) is None, (
            "falha de rede não vira ausência: lista vazia diria que a empresa não paga provento"
        )

    def test_quem_nao_paga_fica_em_cache_como_lista_vazia(self, cache_real, monkeypatch):
        monkeypatch.setattr(universal, "_dividends_sync", lambda symbol: [])
        assert asyncio.run(universal.fetch_dividends("XPTO3")) == []

        def _nao_deveria_buscar(symbol):
            raise AssertionError("resposta vazia legítima já está em cache")

        monkeypatch.setattr(universal, "_dividends_sync", _nao_deveria_buscar)
        assert asyncio.run(universal.fetch_dividends("XPTO3")) == []

    def test_o_universo_vencido_e_servido_quando_a_brapi_cai(self, cache_real, monkeypatch, caplog):
        cache_mod.set(universe._UNIVERSE_CACHE_KEY, ["PETR4", "VALE3"], -3600)
        monkeypatch.setattr(universe, "_fetch_brapi_list", list)

        with caplog.at_level("WARNING", logger=universe.logger.name):
            tickers = universe.get_universe()

        assert tickers == ["PETR4", "VALE3"], (
            "com a BRAPI fora do ar e o universo vencido há uma hora, a varredura inteira "
            "esvaziava: o Descobrir ficava sem nada por falta de uma lista de tickers"
        )
        idade = re.search(r"vencido há (\d+) s", caplog.text)
        assert idade and 3600 <= int(idade.group(1)) < 3700, (
            "o vencido servido precisa dizer a idade no log"
        )
        assert cache_mod.get(universe._UNIVERSE_CACHE_KEY) is None, (
            "servir o vencido não o regrava como válido: a idade sumiria"
        )

    def test_sem_universo_em_cache_a_ausencia_se_declara(self, cache_real, monkeypatch, caplog):
        monkeypatch.setattr(universe, "_fetch_brapi_list", list)

        with caplog.at_level("WARNING", logger=universe.logger.name):
            assert universe.get_universe() == []

        assert "não há universo em cache" in caplog.text

    def test_com_a_brapi_de_pe_o_universo_vencido_e_substituido(self, cache_real):
        cache_mod.set(universe._UNIVERSE_CACHE_KEY, ["XPTO3"], -3600)

        tickers = universe.get_universe()

        assert "XPTO3" not in tickers and tickers, "o vencido é recurso, não preferência"
        assert cache_mod.get(universe._UNIVERSE_CACHE_KEY) == tickers


class TestFalhaDaFonteNaoEListaVazia:
    def test_chamada_que_falhou_nao_devolve_proventos(self, monkeypatch):
        monkeypatch.setattr(universal, "_brapi_raw", lambda base: {})
        monkeypatch.setattr(universal, "_ler_raw", lambda base: None)

        assert universal._dividends_brapi("PETR4") is None

    def test_ticker_sem_resultado_e_lista_vazia(self, monkeypatch):
        monkeypatch.setattr(universal, "_brapi_raw", lambda base: {})
        monkeypatch.setattr(universal, "_ler_raw", lambda base: {})

        assert universal._dividends_brapi("XPTO3") == []


class TestProventoQueNaoChegou:
    def test_acao_cala_em_vez_de_crescer_no_maximo(self):
        r = _acao(dividends=None)

        assert r.fair_low is None
        assert _principal(r)["status"] == "sem_dado"
        assert "não chegou" in _principal(r)["note"], (
            "sem o histórico de proventos o payout é desconhecido; tratá-lo como zero põe a "
            "retenção em 100% e o crescimento no máximo, o cenário mais otimista"
        )

    def test_quem_de_fato_nao_paga_cresce_pelo_roe(self):
        r = _acao(dividends=[])

        assert r.premises["payout"] == 0.0
        assert r.premises["growth"] == pytest.approx(min(0.15, MAX_GROWTH))

    def test_fii_cala_quando_a_distribuicao_nao_chegou(self):
        r = _fii(dividends=None)

        assert r.fair_low is None
        assert "não chegou" in _principal(r)["note"]


class TestAnosComPagamento:
    def test_serie_com_buracos_nao_confirma_o_lucro(self):
        r = _acao(dividends=_anos([0.6, 0.0, 0.0, 0.0, 0.6]))

        bazin = next(m for m in r.methods if m["method"] == "bazin")
        assert bazin["status"] == "sem_dado", (
            "dois pagamentos em cinco anos não são três anos de dividendo: a extensão da série não "
            "é a série"
        )

    def test_fii_com_ano_sem_distribuicao_e_fragil(self):
        r = _fii(dividends=_anos([9.5, 0.0, 9.5], inicio=2023))

        assert r.band_quality == "fragil"
        assert any("2 ano(s) completo(s) com pagamento" in q for q in r.quality_reasons)


class TestTaxaRastreavel:
    def test_as_premissas_dizem_de_onde_veio_a_taxa(self):
        taxas = rates_for_valuation(
            {"selic_media_10a": 10.0, "source": "bcb_cache_vencido", "fetched_at": 1_790_000_000.0}
        )
        p = _acao(rates=taxas, reference=datetime(2026, 9, 23, 15, tzinfo=UTC)).premises

        assert p["rate_source"] == "bcb_cache_vencido", (
            "taxa servida de cache vencido precisa aparecer como tal, com idade"
        )
        assert p["rates_as_of"] == 1_790_000_000.0
        assert p["selic_pct"] == 10.0
        assert p["reference_date"] == "2026-09-23", (
            "sem a data de referência, a janela de dividendos não se reproduz depois"
        )
