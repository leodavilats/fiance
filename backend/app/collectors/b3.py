from __future__ import annotations

import asyncio

import logging

from typing import Dict, List, Optional

import httpx

from app.core import cache

from app.core.config import get_settings

from app.models.company import CompanyFundamentals

logger = logging.getLogger(__name__)

BRAPI_BASE = "https://brapi.dev/api"

FUND_TTL = 6 * 3600

HIST_TTL = 12 * 3600

def _norm_dy(v) -> Optional[float]:

    try:

        if v is None:

            return None

        f = float(v)

        if f <= 0:

            return 0.0

        # Se valor já é >= 1, provavelmente já está em percentual

        if f >= 1.0:

            # Valores > 30% são extremamente raros, provavel erro de dados

            if f > 30.0:

                logger.warning(f"DY suspeito (já em %): {f:.1f}% - limitando a 15%")

                return 15.0

            return f

        # Valor em decimal, converte para percentual

        return f * 100

        return result

    except Exception:

        return None

async def _fetch_brapi(client: httpx.AsyncClient, ticker: str, token: str) -> Optional[CompanyFundamentals]:

    params = {

        "modules": "summaryProfile,defaultKeyStatistics,financialData",

        "fundamental": "true",

    }

    if token:

        params["token"] = token

    try:

        r = await client.get(f"{BRAPI_BASE}/quote/{ticker}", params=params, timeout=15.0)

        r.raise_for_status()

        data = r.json()

    except Exception as e:

        logger.warning("brapi falhou para %s: %s", ticker, e)

        return None

    results = data.get("results") or []

    if not results:

        return None

    item = results[0]

    profile = (item.get("summaryProfile") or {})

    stats = (item.get("defaultKeyStatistics") or {})

    fin = (item.get("financialData") or {})

    def pct(v):

        return float(v) * 100 if v is not None else None

    return CompanyFundamentals(

        ticker=ticker,

        name=item.get("longName") or item.get("shortName"),

        sector=profile.get("sector"),

        price=item.get("regularMarketPrice"),

        market_cap=item.get("marketCap"),

        pe_ratio=item.get("priceEarnings"),

        pb_ratio=stats.get("priceToBook"),

        roe=pct(fin.get("returnOnEquity")),

        dividend_yield=_norm_dy(item.get("dividendYield")),

        debt_to_equity=fin.get("debtToEquity"),

        profit_margin=pct(fin.get("profitMargins")),

        revenue_growth=pct(fin.get("revenueGrowth")),

    )

def _fetch_yfinance_sync(ticker: str) -> Optional[CompanyFundamentals]:

    try:

        import yfinance as yf

    except ImportError:

        return None

    try:

        t = yf.Ticker(f"{ticker}.SA")

        info = t.info or {}

        if not info.get("regularMarketPrice") and not info.get("currentPrice"):

            return None

    except Exception as e:

        logger.warning("yfinance falhou para %s: %s", ticker, e)

        return None

    def pct(v):

        return float(v) * 100 if v is not None else None

    return CompanyFundamentals(

        ticker=ticker,

        name=info.get("longName") or info.get("shortName"),

        sector=info.get("sector"),

        price=info.get("currentPrice") or info.get("regularMarketPrice"),

        market_cap=info.get("marketCap"),

        pe_ratio=info.get("trailingPE"),

        pb_ratio=info.get("priceToBook"),

        roe=pct(info.get("returnOnEquity")),

        dividend_yield=_norm_dy(info.get("dividendYield")),

        debt_to_equity=info.get("debtToEquity"),

        profit_margin=pct(info.get("profitMargins")),

        revenue_growth=pct(info.get("revenueGrowth")),

    )

async def fetch_one(client: httpx.AsyncClient, ticker: str, token: str) -> Optional[CompanyFundamentals]:

    cached = cache.get(f"fund:{ticker}")

    if cached:

        return CompanyFundamentals.model_validate(cached)

    data = await _fetch_brapi(client, ticker, token)

    if not data or not data.price:

        data = await asyncio.to_thread(_fetch_yfinance_sync, ticker)

    if data and data.price:

        cache.set(f"fund:{ticker}", data.model_dump(), FUND_TTL)

    return data

async def fetch_universe(tickers: List[str]) -> List[CompanyFundamentals]:

    settings = get_settings()

    async with httpx.AsyncClient() as client:

        tasks = [fetch_one(client, t, settings.brapi_token) for t in tickers]

        results = await asyncio.gather(*tasks, return_exceptions=True)

    out: List[CompanyFundamentals] = []

    for t, r in zip(tickers, results):

        if isinstance(r, Exception):

            logger.warning("erro coletando %s: %s", t, r)

            continue

        if r is None:

            logger.info("sem dados para %s", t)

            continue

        out.append(r)

    return out

def _fetch_history_sync(ticker: str, period: str = "2y") -> Dict[str, float]:

    try:

        import yfinance as yf

    except ImportError:

        return {}

    try:

        df = yf.Ticker(f"{ticker}.SA").history(period=period, auto_adjust=True)

    except Exception as e:

        logger.warning("histórico falhou %s: %s", ticker, e)

        return {}

    if df is None or df.empty:

        return {}

    return {idx.strftime("%Y-%m-%d"): float(row.Close) for idx, row in df.iterrows()}

async def fetch_history(tickers: List[str], period: str = "2y") -> Dict[str, Dict[str, float]]:

    out: Dict[str, Dict[str, float]] = {}

    async def _one(tk: str) -> None:

        ck = f"hist:{tk}:{period}"

        cached = cache.get(ck)

        if cached:

            out[tk] = cached

            return

        series = await asyncio.to_thread(_fetch_history_sync, tk, period)

        if series:

            cache.set(ck, series, HIST_TTL)

            out[tk] = series

    await asyncio.gather(*[_one(t) for t in tickers])

    return out

