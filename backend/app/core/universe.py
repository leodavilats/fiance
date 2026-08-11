from __future__ import annotations

import logging
import re

import httpx

from app.core import cache
from app.core.config import get_settings

logger = logging.getLogger(__name__)

_LIST_URL = "https://brapi.dev/api/quote/list"
_UNIVERSE_CACHE_KEY = "brapi_universe_v1"
_STOCKS_RAW_CACHE_KEY = "brapi_stocks_raw_v1"
_UNIVERSE_TTL = 24 * 3600

# Lotes fracionários (ex.: PETR4F) são o mesmo ativo do ticker "cheio"
# (PETR4) negociado em quantidade fracionada — mesmo fundamento, mesmo
# preço-base. Sem filtrar, competem pelas vagas do top-N como se fossem
# ativos distintos.
_FRACTIONAL_LOT = re.compile(r"^[A-Z]{4}\d{1,2}F$")

# Ações americanas e cripto não vêm da BRAPI (Finnhub/CoinGecko não têm um
# endpoint de "listar tudo" prático) — mantidos como uma lista curta e
# curada manualmente.
CURATED_US_NAMES = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corp.",
    "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.",
    "META": "Meta Platforms Inc.",
    "NVDA": "NVIDIA Corp.",
    "TSLA": "Tesla Inc.",
    "NFLX": "Netflix Inc.",
    "JNJ": "Johnson & Johnson",
    "JPM": "JPMorgan Chase & Co.",
    "V": "Visa Inc.",
    "KO": "The Coca-Cola Company",
    "PEP": "PepsiCo Inc.",
}

CURATED_CRYPTO_NAMES = {
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "SOL-USD": "Solana",
    "BNB-USD": "BNB",
    "XRP-USD": "XRP",
    "ADA-USD": "Cardano",
    "DOGE-USD": "Dogecoin",
    "DOT-USD": "Polkadot",
    "AVAX-USD": "Avalanche",
}

CURATED_US = list(CURATED_US_NAMES)
CURATED_CRYPTO = list(CURATED_CRYPTO_NAMES)


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
    """/quote/list completo, cacheado — usado tanto para montar o universo
    quanto para o mapa de setores (é a única fonte que traz `sector`; o
    endpoint de cotação individual não devolve esse campo)."""

    cached = cache.get(_STOCKS_RAW_CACHE_KEY)
    if cached is not None:
        return cached

    stocks = _fetch_brapi_list()
    if stocks:
        cache.set(_STOCKS_RAW_CACHE_KEY, stocks, _UNIVERSE_TTL)
    return stocks


def get_sector_map() -> dict[str, str]:
    """Ticker (sem sufixo) → setor bruto da BRAPI (taxonomia em inglês,
    tipo 'Finance', 'Technology Services'). Tradução pro português fica a
    cargo do frontend (UiHelperService.translateSector)."""

    stocks = _get_brapi_stocks_cached()
    return {s["stock"]: s["sector"] for s in stocks if s.get("stock") and s.get("sector")}


def _build_brapi_universe(
    max_stocks: int = 150, max_fiis: int = 60, max_bdrs: int = 40
) -> list[str]:
    """Monta o universo de ações/FIIs/BDRs a partir de TODOS os tickers
    negociados na B3 (endpoint /quote/list da BRAPI), sem curadoria manual —
    ordenado por relevância (market cap / volume) e limitado por categoria
    para manter o tempo de varredura sob controle (~300 tickers no total,
    igual ao universo estático anterior)."""

    stocks = _get_brapi_stocks_cached()
    if not stocks:
        return []

    stocks = [s for s in stocks if not _FRACTIONAL_LOT.match(s.get("stock") or "")]

    br_stocks = [
        s for s in stocks if s.get("subType") == "stock" and (s.get("market_cap") or 0) > 0
    ]
    fiis = [s for s in stocks if s.get("subType") == "fii" and (s.get("volume") or 0) > 0]
    bdrs = [s for s in stocks if s.get("subType") == "bdr" and (s.get("market_cap") or 0) > 0]

    br_stocks.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)
    fiis.sort(key=lambda s: s.get("volume") or 0, reverse=True)
    bdrs.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)

    tickers = (
        [s["stock"] for s in br_stocks[:max_stocks]]
        + [s["stock"] for s in fiis[:max_fiis]]
        + [s["stock"] for s in bdrs[:max_bdrs]]
    )
    return tickers


def get_universe() -> list[str]:
    """Universo completo (B3 dinâmico via BRAPI + US/cripto curados).
    Cacheado por 24h — a composição da B3 não muda de um dia pro outro.
    Se a BRAPI falhar, cai para o DEFAULT_UNIVERSE estático (.env)."""

    cached = cache.get(_UNIVERSE_CACHE_KEY)
    if cached is not None:
        return cached

    brapi_tickers = _build_brapi_universe()
    if not brapi_tickers:
        logger.warning("Usando DEFAULT_UNIVERSE estático — lista dinâmica da BRAPI falhou.")
        return get_settings().universe

    universe = brapi_tickers + CURATED_US + CURATED_CRYPTO
    cache.set(_UNIVERSE_CACHE_KEY, universe, _UNIVERSE_TTL)
    return universe


def search_universe(query: str, limit: int = 10) -> list[dict]:
    """Busca ticker+nome por prefixo/substring — usado pelo autocomplete de
    ticker no web/mobile. Varre TODA a lista de ações/FIIs/BDRs da B3 (não só
    o universo curado/limitado de `get_universe()`), mais as listas curadas
    de ações US e cripto."""
    q = query.strip().upper()
    if not q:
        return []

    seen: set[str] = set()
    results: list[dict] = []

    for s in _get_brapi_stocks_cached():
        ticker = (s.get("stock") or "").upper()
        name = s.get("name") or ""
        if not ticker or ticker in seen or _FRACTIONAL_LOT.match(ticker):
            continue
        if q in ticker or q in name.upper():
            seen.add(ticker)
            results.append({"ticker": ticker, "name": name})

    for ticker, name in {**CURATED_US_NAMES, **CURATED_CRYPTO_NAMES}.items():
        if ticker in seen:
            continue
        if q in ticker or q in name.upper():
            seen.add(ticker)
            results.append({"ticker": ticker, "name": name})

    # Prioriza tickers que começam com a busca sobre matches no meio da
    # string/nome, depois ordem alfabética.
    results.sort(key=lambda r: (not r["ticker"].startswith(q), r["ticker"]))
    return results[:limit]
