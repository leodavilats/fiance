from __future__ import annotations

import logging
import re
import threading
import time

import httpx

from app.core import cache
from app.core.config import get_settings

logger = logging.getLogger(__name__)

_LIST_URL = "https://brapi.dev/api/quote/list"
_UNIVERSE_CACHE_KEY = "brapi_universe_v1"
_STOCKS_RAW_CACHE_KEY = "brapi_stocks_raw_v1"
_UNIVERSE_TTL = 24 * 3600

# PETR4F etc. são lotes fracionários do mesmo ativo "cheio" (PETR4); sem
# filtrar, competem pelas vagas do top-N como se fossem ativos distintos.
_FRACTIONAL_LOT = re.compile(r"^[A-Z]{4}\d{1,2}F$")

# ETFs líquidos da B3 usados como seed/fallback quando o subType retornado
# pela BRAPI não vier marcado corretamente. Fonte única — antes havia uma
# segunda cópia em app.collectors.universal mantida em sincronia à mão.
KNOWN_ETFS = {
    "BOVA11",
    "BOVV11",
    "SMAL11",
    "IVVB11",
    "PIBB11",
    "DIVO11",
    "GOVE11",
    "MATB11",
    "FIND11",
    "ISUS11",
    "ECOO11",
    "HASH11",
    "BITH11",
}


def _fetch_brapi_list() -> list[dict]:
    settings = get_settings()
    try:
        resp = httpx.get(_LIST_URL, params={"token": settings.brapi_token}, timeout=20)
        resp.raise_for_status()
        return resp.json().get("stocks") or []
    except Exception as e:
        logger.warning("Falha ao buscar lista de tickers da BRAPI: %s", e)
        return []


def _get_brapi_stocks_cached() -> list[dict]:
    cached = cache.get(_STOCKS_RAW_CACHE_KEY)
    if cached is not None:
        return cached

    stocks = _fetch_brapi_list()
    if stocks:
        cache.set(_STOCKS_RAW_CACHE_KEY, stocks, _UNIVERSE_TTL)
    return stocks


# Índices derivados da lista da BRAPI, memoizados em processo. Sem isso um
# scan completo fazia ~280 leituras do blob no SQLite + 280 json.loads + 280
# construções de dict (get_sector_map é chamado por ticker), e cada tecla do
# autocomplete desserializava a lista inteira.
_MEMO_TTL = 15 * 60
_memo_lock = threading.Lock()
_memo: dict[str, tuple[float, object]] = {}


def _memoized(key: str, build):
    now = time.monotonic()
    cached = _memo.get(key)
    if cached is not None and (now - cached[0]) < _MEMO_TTL:
        return cached[1]

    with _memo_lock:
        cached = _memo.get(key)
        if cached is not None and (time.monotonic() - cached[0]) < _MEMO_TTL:
            return cached[1]
        value = build()
        _memo[key] = (time.monotonic(), value)
        return value


def invalidate_universe_memo() -> None:
    """Descarta os índices em processo (chamado ao limpar o cache)."""
    with _memo_lock:
        _memo.clear()


def get_sector_map() -> dict[str, str]:
    def _build() -> dict[str, str]:
        stocks = _get_brapi_stocks_cached()
        return {s["stock"]: s["sector"] for s in stocks if s.get("stock") and s.get("sector")}

    return _memoized("sector_map", _build)


def _get_search_index() -> list[tuple[str, str, str]]:
    """(ticker, nome, NOME_UPPER) de cada papel elegível, construído uma vez."""

    def _build() -> list[tuple[str, str, str]]:
        seen: set[str] = set()
        index: list[tuple[str, str, str]] = []
        for s in _get_brapi_stocks_cached():
            ticker = (s.get("stock") or "").upper()
            if not ticker or ticker in seen or _FRACTIONAL_LOT.match(ticker):
                continue
            seen.add(ticker)
            name = s.get("name") or ""
            index.append((ticker, name, name.upper()))
        return index

    return _memoized("search_index", _build)


def _build_brapi_universe(
    max_stocks: int = 150, max_fiis: int = 60, max_bdrs: int = 40, max_etfs: int = 30
) -> list[str]:
    stocks = _get_brapi_stocks_cached()
    if not stocks:
        return []

    stocks = [s for s in stocks if not _FRACTIONAL_LOT.match(s.get("stock") or "")]

    br_stocks = [
        s for s in stocks if s.get("subType") == "stock" and (s.get("market_cap") or 0) > 0
    ]
    fiis = [s for s in stocks if s.get("subType") == "fii" and (s.get("volume") or 0) > 0]
    bdrs = [s for s in stocks if s.get("subType") == "bdr" and (s.get("market_cap") or 0) > 0]
    etfs = [s for s in stocks if s.get("subType") == "etf" and (s.get("volume") or 0) > 0]

    br_stocks.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)
    fiis.sort(key=lambda s: s.get("volume") or 0, reverse=True)
    bdrs.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)
    etfs.sort(key=lambda s: s.get("volume") or 0, reverse=True)

    etf_tickers = {s["stock"] for s in etfs[:max_etfs]} | KNOWN_ETFS

    tickers = (
        [s["stock"] for s in br_stocks[:max_stocks]]
        + [s["stock"] for s in fiis[:max_fiis]]
        + [s["stock"] for s in bdrs[:max_bdrs]]
        + sorted(etf_tickers)
    )
    return tickers


def get_universe() -> list[str]:
    cached = cache.get(_UNIVERSE_CACHE_KEY)
    if cached is not None:
        return cached

    brapi_tickers = _build_brapi_universe()
    if not brapi_tickers:
        logger.warning("Usando DEFAULT_UNIVERSE estático — lista dinâmica da BRAPI falhou.")
        return get_settings().universe

    cache.set(_UNIVERSE_CACHE_KEY, brapi_tickers, _UNIVERSE_TTL)
    return brapi_tickers


def search_universe(query: str, limit: int = 10) -> list[dict]:
    q = query.strip().upper()
    if not q:
        return []

    results = [
        {"ticker": ticker, "name": name}
        for ticker, name, name_upper in _get_search_index()
        if q in ticker or q in name_upper
    ]

    results.sort(key=lambda r: (not r["ticker"].startswith(q), r["ticker"]))
    return results[:limit]
