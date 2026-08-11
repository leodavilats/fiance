from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import UTC
from typing import Literal

import httpx

from app.core import cache
from app.core.config import get_settings
from app.core.universe import get_sector_map

logger = logging.getLogger(__name__)

AssetType = Literal["br_stock", "bdr", "fii", "us_stock", "crypto"]

FUND_TTL = 2 * 3600
HIST_TTL = 12 * 3600
DIV_TTL = 24 * 3600

_FETCH_SEMAPHORE = asyncio.Semaphore(30)

_CRYPTO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "ADA": "cardano",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "AVAX": "avalanche-2",
    "MATIC": "matic-network",
    "LTC": "litecoin",
    "LINK": "chainlink",
    "ATOM": "cosmos",
    "BCH": "bitcoin-cash",
}

KNOWN_UNITS = {
    "SANB11",
    "TAEE11",
    "BPAC11",
    "KLBN11",
    "SAPR11",
    "ALUP11",
    "ENGI11",
    "IGTI11",
    "RNEW11",
    "BRBI11",
}

_BDR = re.compile(r"^[A-Z]{4}3\d$")
_ENDS_11 = re.compile(r"^[A-Z]{4}11$")
_BR_STOCK = re.compile(r"^[A-Z]{4}\d{1,2}$")

_BRAPI_BASE = "https://brapi.dev/api"
_FINNHUB_BASE = "https://finnhub.io/api/v1"
_COINGECKO_BASE = "https://api.coingecko.com/api/v3"


def detect_type(symbol: str) -> AssetType:
    s = symbol.strip().upper()
    base = s[:-3] if s.endswith(".SA") else s

    if "-USD" in s or "-BRL" in s or base in _CRYPTO_IDS:
        return "crypto"

    if _BDR.match(base):
        return "bdr"

    if _ENDS_11.match(base):
        return "br_stock" if base in KNOWN_UNITS else "fii"

    if _BR_STOCK.match(base):
        return "br_stock"

    return "us_stock"


def _base_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if s.endswith(".SA"):
        return s[:-3]
    if "-USD" in s or "-BRL" in s:
        return s.split("-")[0]
    return s


def to_yf_symbol(symbol: str, asset_type: AssetType | None = None) -> str:
    s = symbol.strip().upper()
    t = asset_type or detect_type(s)

    if t in ("br_stock", "fii", "bdr"):
        return s if s.endswith(".SA") else f"{s}.SA"

    if t == "crypto":
        if "-USD" in s or "-BRL" in s:
            return s
        return f"{s}-USD"

    return s


@dataclass
class AssetSnapshot:
    symbol: str
    yf_symbol: str
    asset_type: AssetType
    name: str | None
    sector: str | None
    currency: str | None
    price: float | None
    market_cap: float | None
    pe_ratio: float | None
    pb_ratio: float | None
    eps: float | None
    book_value: float | None
    roe: float | None
    dividend_yield: float | None
    debt_to_equity: float | None
    profit_margin: float | None
    revenue_growth: float | None
    fifty_two_week_high: float | None
    fifty_two_week_low: float | None

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def _safe_float(v) -> float | None:
    try:
        return float(v) if v is not None else None
    except (ValueError, TypeError):
        return None


def _safe_pct(v) -> float | None:
    try:
        if v is None:
            return None
        f = float(v)
        if f > 1.0:
            return f
        return f * 100.0
    except (ValueError, TypeError):
        return None


def _calculate_dividend_yield(dividends_12m: float, current_price: float) -> float | None:
    try:
        if current_price <= 0 or dividends_12m < 0:
            return None
        return round((dividends_12m / current_price) * 100, 2)
    except (ValueError, TypeError, ZeroDivisionError):
        return None


# Uma única chamada combinada (fundamental+dividends+range) evita 3 requisições
# HTTP separadas por ticker; o resultado bruto é reaproveitado por fetch_asset/
# fetch_dividends/fetch_history_universal via cache.
_BRAPI_RAW_TTL = FUND_TTL


def _brapi_raw(base: str) -> dict:
    ck = f"brapi_raw:{base}"
    cached = cache.get(ck)
    if cached is not None:
        return cached

    settings = get_settings()
    try:
        resp = httpx.get(
            f"{_BRAPI_BASE}/quote/{base}",
            params={
                "token": settings.brapi_token,
                "fundamental": "true",
                # "dividends": "true" bloqueado no plano gratuito (403 FEATURE_NOT_AVAILABLE);
                # plano gratuito também só aceita ranges curtos (1d/5d/1mo/3mo), outro valor = 400.
                "range": "3mo",
                "interval": "1d",
            },
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json().get("results") or []
        if not results:
            return {}
        r = results[0]
    except Exception as e:
        logger.warning("brapi falhou %s: %s", base, e)
        return {}

    cache.set(ck, r, _BRAPI_RAW_TTL)
    return r


def _fetch_brapi(symbol: str, asset_type: AssetType) -> AssetSnapshot | None:
    base = _base_symbol(symbol)
    r = _brapi_raw(base)
    if not r:
        return None

    price = _safe_float(r.get("regularMarketPrice"))
    if not price:
        return None

    t = asset_type
    name = r.get("longName") or r.get("shortName") or base
    if t == "fii" and any(tok in name.upper() for tok in ("UNT", "UNIT", "UNITS")):
        t = "br_stock"

    dividend_yield = None
    div_data = r.get("dividendsData") or {}
    cash_divs = div_data.get("cashDividends") or []
    try:
        total_12m = sum(_safe_float(d.get("rate")) or 0 for d in cash_divs[:12])
        if total_12m > 0:
            dividend_yield = _calculate_dividend_yield(total_12m, price)
    except Exception:
        pass

    # /quote não devolve `sector` no plano gratuito; usa mapa do /quote/list.
    sector = r.get("sector") or get_sector_map().get(base)

    return AssetSnapshot(
        symbol=symbol.upper(),
        yf_symbol=to_yf_symbol(symbol, t),
        asset_type=t,
        name=name,
        sector=sector,
        currency=r.get("currency") or "BRL",
        price=price,
        market_cap=_safe_float(r.get("marketCap")),
        pe_ratio=_safe_float(r.get("priceEarnings")),
        pb_ratio=_safe_float(r.get("priceToBook") or r.get("pvp")),
        eps=_safe_float(r.get("earningsPerShare")),
        book_value=_safe_float(r.get("bookValue")),
        roe=_safe_pct(r.get("returnOnEquity")),
        dividend_yield=dividend_yield,
        debt_to_equity=_safe_float(r.get("debtToEquity")),
        profit_margin=_safe_pct(r.get("profitMargins")),
        revenue_growth=_safe_pct(r.get("revenueGrowth")),
        fifty_two_week_high=_safe_float(r.get("fiftyTwoWeekHigh")),
        fifty_two_week_low=_safe_float(r.get("fiftyTwoWeekLow")),
    )


def _history_brapi(symbol: str, period: str = "1y") -> dict[str, float]:
    base = _base_symbol(symbol)
    r = _brapi_raw(base)
    prices = r.get("historicalDataPrice") or []

    days_map = {"5d": 5, "6mo": 182, "1y": 365, "2y": 730, "max": 10_000}
    max_days = days_map.get(period, 365)
    if max_days < 730:
        prices = prices[-max_days:]

    out: dict[str, float] = {}
    for p in prices:
        close = _safe_float(p.get("close"))
        ts = p.get("date")
        if close is None or ts is None:
            continue
        try:
            from datetime import datetime

            day = datetime.fromtimestamp(int(ts), tz=UTC).strftime("%Y-%m-%d")
            out[day] = close
        except Exception:
            continue
    return out


def _dividends_brapi(symbol: str) -> list[dict[str, float]]:
    base = _base_symbol(symbol)
    r = _brapi_raw(base)
    cash_divs = (r.get("dividendsData") or {}).get("cashDividends") or []

    out: list[dict[str, float]] = []
    for d in cash_divs:
        date = d.get("paymentDate") or d.get("approvedOn")
        value = _safe_float(d.get("rate"))
        if date and value is not None:
            out.append({"date": str(date)[:10], "value": value})
    return sorted(out, key=lambda x: x["date"])


def _fetch_finnhub(symbol: str) -> AssetSnapshot | None:
    settings = get_settings()
    if not settings.finnhub_api_key:
        return None

    base = _base_symbol(symbol)
    try:
        quote = httpx.get(
            f"{_FINNHUB_BASE}/quote",
            params={"symbol": base, "token": settings.finnhub_api_key},
            timeout=10,
        ).json()
        metric = httpx.get(
            f"{_FINNHUB_BASE}/stock/metric",
            params={"symbol": base, "metric": "all", "token": settings.finnhub_api_key},
            timeout=10,
        ).json()
        profile = httpx.get(
            f"{_FINNHUB_BASE}/stock/profile2",
            params={"symbol": base, "token": settings.finnhub_api_key},
            timeout=10,
        ).json()
    except Exception as e:
        logger.warning("finnhub falhou %s: %s", base, e)
        return None

    price = _safe_float(quote.get("c"))
    if not price:
        return None

    m = metric.get("metric") or {}

    return AssetSnapshot(
        symbol=symbol.upper(),
        yf_symbol=base,
        asset_type="us_stock",
        name=profile.get("name") or base,
        sector=profile.get("finnhubIndustry"),
        currency=profile.get("currency") or "USD",
        price=price,
        market_cap=_safe_float(profile.get("marketCapitalization")),
        pe_ratio=_safe_float(m.get("peBasicExclExtraTTM")),
        pb_ratio=_safe_float(m.get("pbAnnual")),
        eps=_safe_float(m.get("epsTTM")),
        book_value=_safe_float(m.get("bookValuePerShareAnnual")),
        roe=_safe_pct(m.get("roeTTM")),
        dividend_yield=_safe_pct(m.get("dividendYieldIndicatedAnnual")),
        debt_to_equity=_safe_float(m.get("totalDebt/totalEquityAnnual")),
        profit_margin=_safe_pct(m.get("netProfitMarginTTM")),
        revenue_growth=_safe_pct(m.get("revenueGrowthTTMYoy")),
        fifty_two_week_high=_safe_float(m.get("52WeekHigh")),
        fifty_two_week_low=_safe_float(m.get("52WeekLow")),
    )


def _fetch_coingecko(symbol: str) -> AssetSnapshot | None:
    base = _base_symbol(symbol)
    coin_id = _CRYPTO_IDS.get(base)
    if not coin_id:
        return None

    try:
        data = httpx.get(
            f"{_COINGECKO_BASE}/simple/price",
            params={
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_market_cap": "true",
                "include_24hr_change": "true",
            },
            timeout=10,
        ).json()
        coin = data.get(coin_id) or {}
    except Exception as e:
        logger.warning("coingecko falhou %s: %s", base, e)
        return None

    price = _safe_float(coin.get("usd"))
    if not price:
        return None

    return AssetSnapshot(
        symbol=symbol.upper(),
        yf_symbol=f"{base}-USD",
        asset_type="crypto",
        name=base,
        sector="Criptomoeda",
        currency="USD",
        price=price,
        market_cap=_safe_float(coin.get("usd_market_cap")),
        pe_ratio=None,
        pb_ratio=None,
        eps=None,
        book_value=None,
        roe=None,
        dividend_yield=None,
        debt_to_equity=None,
        profit_margin=None,
        revenue_growth=None,
        fifty_two_week_high=None,
        fifty_two_week_low=None,
    )


def _history_coingecko(symbol: str, period: str = "1y") -> dict[str, float]:
    base = _base_symbol(symbol)
    coin_id = _CRYPTO_IDS.get(base)
    if not coin_id:
        return {}

    days_map = {"5d": 5, "6mo": 180, "1y": 365, "2y": 730, "max": "max"}
    days = days_map.get(period, 365)

    try:
        data = httpx.get(
            f"{_COINGECKO_BASE}/coins/{coin_id}/market_chart",
            params={"vs_currency": "usd", "days": days},
            timeout=15,
        ).json()
        prices = data.get("prices") or []
    except Exception as e:
        logger.warning("coingecko hist falhou %s: %s", base, e)
        return {}

    out: dict[str, float] = {}
    for ts_ms, price in prices:
        try:
            from datetime import datetime

            day = datetime.fromtimestamp(ts_ms / 1000, tz=UTC).strftime("%Y-%m-%d")
            out[day] = float(price)
        except Exception:
            continue
    return out


def _fetch_sync(symbol: str, asset_type: AssetType | None = None) -> AssetSnapshot | None:
    t = asset_type or detect_type(symbol)

    if t in ("br_stock", "fii", "bdr"):
        return _fetch_brapi(symbol, t)
    if t == "crypto":
        return _fetch_coingecko(symbol)
    return _fetch_finnhub(symbol)


def _history_sync(symbol: str, period: str = "1y") -> dict[str, float]:
    t = detect_type(symbol)

    if t in ("br_stock", "fii", "bdr"):
        return _history_brapi(symbol, period)
    if t == "crypto":
        return _history_coingecko(symbol, period)
    return {}


def _dividends_sync(symbol: str) -> list[dict[str, float]]:
    t = detect_type(symbol)

    if t in ("br_stock", "fii", "bdr"):
        return _dividends_brapi(symbol)
    return []


async def fetch_asset(symbol: str, asset_type: AssetType | None = None) -> AssetSnapshot | None:
    ck = f"uasset:{symbol.upper()}"
    cached = cache.get(ck)
    if cached:
        try:
            return AssetSnapshot(**cached)
        except Exception:
            pass

    async with _FETCH_SEMAPHORE:
        cached = cache.get(ck)
        if cached:
            try:
                return AssetSnapshot(**cached)
            except Exception:
                pass

        snap = await asyncio.to_thread(_fetch_sync, symbol, asset_type)

    if snap:
        cache.set(ck, snap.to_dict(), FUND_TTL)

    return snap


async def fetch_many(symbols: list[str]) -> list[AssetSnapshot]:
    tasks = [fetch_asset(s) for s in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    out: list[AssetSnapshot] = []
    for r in results:
        if isinstance(r, AssetSnapshot):
            out.append(r)
        elif isinstance(r, Exception):
            logger.debug("fetch_many: erro ignorado — %s", r)

    return out


async def fetch_history_universal(symbol: str, period: str = "1y") -> dict[str, float]:
    ck = f"uhist:{symbol.upper()}:{period}"
    cached = cache.get(ck)
    if cached:
        return cached

    series = await asyncio.to_thread(_history_sync, symbol, period)

    if series:
        cache.set(ck, series, HIST_TTL)

    return series


async def fetch_dividends(symbol: str) -> list[dict[str, float]]:
    ck = f"udiv:{symbol.upper()}"
    cached = cache.get(ck)
    if cached:
        return cached

    data = await asyncio.to_thread(_dividends_sync, symbol)

    if data:
        cache.set(ck, data, DIV_TTL)

    return data
