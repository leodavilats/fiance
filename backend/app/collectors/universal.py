from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Literal

from app.core import cache

logger = logging.getLogger(__name__)

AssetType = Literal["br_stock", "fii", "us_stock", "crypto"]

FUND_TTL = 2 * 3600
HIST_TTL = 12 * 3600
DIV_TTL = 24 * 3600

_FETCH_SEMAPHORE = asyncio.Semaphore(10)

_BR_STOCK = re.compile(r"^[A-Z]{4}\d{1,2}$")

_FII = re.compile(r"^[A-Z]{4}11$")

_CRYPTO_HINT = re.compile(r"^[A-Z]{2,10}(-USD|-BRL)?$")


def detect_type(symbol: str) -> AssetType:

    s = symbol.strip().upper()

    if "-USD" in s or "-BRL" in s:
        return "crypto"

    if _FII.match(s):
        return "fii"

    if _BR_STOCK.match(s):
        return "br_stock"

    if s in {"BTC", "ETH", "SOL", "ADA", "BNB", "XRP", "DOGE", "DOT", "AVAX", "MATIC", "LTC"}:
        return "crypto"

    return "us_stock"


def to_yf_symbol(symbol: str, asset_type: AssetType | None = None) -> str:

    s = symbol.strip().upper()

    t = asset_type or detect_type(s)

    if t in ("br_stock", "fii"):
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


def _fetch_sync(symbol: str, asset_type: AssetType | None = None) -> AssetSnapshot | None:
    try:
        import yfinance as yf

    except ImportError:
        return None

    t = asset_type or detect_type(symbol)

    yf_sym = to_yf_symbol(symbol, t)

    try:
        tk = yf.Ticker(yf_sym)

        info = tk.info or {}

    except Exception as e:
        logger.warning("yfinance falhou %s: %s", yf_sym, e)

        return None

    price = _safe_float(info.get("currentPrice")) or _safe_float(info.get("regularMarketPrice"))

    if not price:
        try:
            hist = tk.history(period="5d", auto_adjust=True)

            if hist is not None and not hist.empty:
                price = float(hist["Close"].iloc[-1])

        except Exception:
            pass

    if not price:
        return None

    dividend_yield = None
    try:
        divs = tk.dividends
        if divs is not None and not divs.empty:
            import pandas as pd

            now = pd.Timestamp.now(tz=divs.index.tz if divs.index.tz else None)
            cutoff = now - pd.Timedelta(days=365)
            recent = divs[divs.index >= cutoff]
            total_12m = recent.sum()
            if total_12m > 0:
                dividend_yield = _calculate_dividend_yield(total_12m, price)
                logger.debug(f"{yf_sym}: DY calculado = {dividend_yield}%")
    except Exception as e:
        logger.debug(f"{yf_sym}: Não foi possível calcular DY: {e}")

        dividend_yield = _safe_pct(info.get("dividendYield"))

    return AssetSnapshot(
        symbol=symbol.upper(),
        yf_symbol=yf_sym,
        asset_type=t,
        name=info.get("longName") or info.get("shortName") or symbol.upper(),
        sector=info.get("sector") or info.get("category"),
        currency=info.get("currency"),
        price=price,
        market_cap=_safe_float(info.get("marketCap")),
        pe_ratio=_safe_float(info.get("trailingPE")),
        pb_ratio=_safe_float(info.get("priceToBook")),
        eps=_safe_float(info.get("trailingEps")),
        book_value=_safe_float(info.get("bookValue")),
        roe=_safe_pct(info.get("returnOnEquity")),
        dividend_yield=dividend_yield,
        debt_to_equity=_safe_float(info.get("debtToEquity")),
        profit_margin=_safe_pct(info.get("profitMargins")),
        revenue_growth=_safe_pct(info.get("revenueGrowth")),
        fifty_two_week_high=_safe_float(info.get("fiftyTwoWeekHigh")),
        fifty_two_week_low=_safe_float(info.get("fiftyTwoWeekLow")),
    )


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


def _history_sync(symbol: str, period: str = "1y") -> dict[str, float]:

    try:
        import yfinance as yf

    except ImportError:
        return {}

    yf_sym = to_yf_symbol(symbol)

    try:
        df = yf.Ticker(yf_sym).history(period=period, auto_adjust=True)

    except Exception as e:
        logger.warning("hist falhou %s: %s", yf_sym, e)

        return {}

    if df is None or df.empty:
        return {}

    return {idx.strftime("%Y-%m-%d"): float(row.Close) for idx, row in df.iterrows()}


async def fetch_history_universal(symbol: str, period: str = "1y") -> dict[str, float]:

    ck = f"uhist:{symbol.upper()}:{period}"

    cached = cache.get(ck)

    if cached:
        return cached

    series = await asyncio.to_thread(_history_sync, symbol, period)

    if series:
        cache.set(ck, series, HIST_TTL)

    return series


def _dividends_sync(symbol: str) -> list[dict[str, float]]:

    try:
        import yfinance as yf

    except ImportError:
        return []

    yf_sym = to_yf_symbol(symbol)

    try:
        s = yf.Ticker(yf_sym).dividends

    except Exception as e:
        logger.warning("div falhou %s: %s", yf_sym, e)

        return []

    if s is None or s.empty:
        return []

    s = s.sort_index()

    out: list[dict[str, float]] = []

    for idx, val in s.items():
        try:
            out.append({"date": idx.strftime("%Y-%m-%d"), "value": float(val)})

        except Exception:
            continue

    return out


async def fetch_dividends(symbol: str) -> list[dict[str, float]]:

    ck = f"udiv:{symbol.upper()}"

    cached = cache.get(ck)

    if cached:
        return cached

    data = await asyncio.to_thread(_dividends_sync, symbol)

    if data:
        cache.set(ck, data, DIV_TTL)

    return data
