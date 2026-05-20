from __future__ import annotations

import asyncio

import logging

import re

from dataclasses import dataclass

from typing import Dict, List, Literal, Optional

from app.core import cache

logger = logging.getLogger(__name__)

AssetType = Literal["br_stock", "fii", "us_stock", "crypto"]

FUND_TTL = 6 * 3600

HIST_TTL = 12 * 3600

DIV_TTL = 24 * 3600

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

def to_yf_symbol(symbol: str, asset_type: Optional[AssetType] = None) -> str:

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

    name: Optional[str]

    sector: Optional[str]

    currency: Optional[str]

    price: Optional[float]

    market_cap: Optional[float]

    pe_ratio: Optional[float]

    pb_ratio: Optional[float]

    eps: Optional[float]

    book_value: Optional[float]

    roe: Optional[float]

    dividend_yield: Optional[float]

    debt_to_equity: Optional[float]

    profit_margin: Optional[float]

    revenue_growth: Optional[float]

    fifty_two_week_high: Optional[float]

    fifty_two_week_low: Optional[float]

    def to_dict(self) -> dict:

        return self.__dict__.copy()

def _pct(v) -> Optional[float]:

    try:

        return float(v) * 100 if v is not None else None

    except Exception:

        return None

def _dy(v) -> Optional[float]:

    try:

        if v is None:

            return None

        f = float(v)

        if f <= 0:

            return 0.0

        # Se valor já é >= 1, provavelmente já está em percentual (APIs devem retornar decimal)

        if f >= 1.0:

            # Valores > 30% são extremamente raros, provavel erro de dados

            if f > 30.0:

                logger.warning(f"DY suspeito (já em %): {f:.1f}% - limitando a 15%")

                return 15.0

            return f

        # Valor em decimal, converte para percentual

        return f * 100

    except Exception:

        return None

def _safe(v) -> Optional[float]:

    try:

        return float(v) if v is not None else None

    except Exception:

        return None

def _fetch_sync(symbol: str, asset_type: Optional[AssetType] = None) -> Optional[AssetSnapshot]:

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

    price = _safe(info.get("currentPrice")) or _safe(info.get("regularMarketPrice"))

    if not price:

        try:

            hist = tk.history(period="5d", auto_adjust=True)

            if hist is not None and not hist.empty:

                price = float(hist["Close"].iloc[-1])

        except Exception:

            pass

    if not price:

        return None

    # Corrigir dividend_yield quando necessário

    dy_from_info = _dy(info.get("dividendYield"))

    

    # Se DY > 15%, provável erro do yfinance para ações brasileiras - calcular manualmente

    if dy_from_info and dy_from_info > 15.0:

        logger.warning(f"{yf_sym}: DY suspeito do yfinance ({dy_from_info}%), calculando manualmente...")

        try:

            divs = tk.dividends

            if divs is not None and not divs.empty:

                import pandas as pd

                now = pd.Timestamp.now(tz=divs.index.tz if divs.index.tz else None)

                cutoff = now - pd.Timedelta(days=365)

                recent = divs[divs.index >= cutoff]

                total_12m = recent.sum()

                dy_from_info = round((total_12m / price * 100), 2) if total_12m > 0 else 0.0

                # Validar DY corrigido - valores > 20% são suspeitos (exceto FIIs)

                max_dy = 25.0 if t == "fii" else 18.0

                if dy_from_info > max_dy:

                    logger.warning(f"{yf_sym}: DY corrigido muito alto ({dy_from_info}%), limitando a {max_dy}%")

                    dy_from_info = max_dy

                else:

                    logger.info(f"{yf_sym}: DY corrigido para {dy_from_info}%")

            else:

                dy_from_info = None

        except Exception as e:

            logger.warning(f"{yf_sym}: Erro ao calcular DY manualmente: {e}")

            dy_from_info = None

    return AssetSnapshot(

        symbol=symbol.upper(),

        yf_symbol=yf_sym,

        asset_type=t,

        name=info.get("longName") or info.get("shortName"),

        sector=info.get("sector") or info.get("category"),

        currency=info.get("currency"),

        price=price,

        market_cap=_safe(info.get("marketCap")),

        pe_ratio=_safe(info.get("trailingPE")),

        pb_ratio=_safe(info.get("priceToBook")),

        eps=_safe(info.get("trailingEps")),

        book_value=_safe(info.get("bookValue")),

        roe=_pct(info.get("returnOnEquity")),

        dividend_yield=dy_from_info,

        debt_to_equity=_safe(info.get("debtToEquity")),

        profit_margin=_pct(info.get("profitMargins")),

        revenue_growth=_pct(info.get("revenueGrowth")),

        fifty_two_week_high=_safe(info.get("fiftyTwoWeekHigh")),

        fifty_two_week_low=_safe(info.get("fiftyTwoWeekLow")),

    )

async def fetch_asset(symbol: str, asset_type: Optional[AssetType] = None) -> Optional[AssetSnapshot]:

    ck = f"uasset:{symbol.upper()}"

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

async def fetch_many(symbols: List[str]) -> List[AssetSnapshot]:

    tasks = [fetch_asset(s) for s in symbols]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    out: List[AssetSnapshot] = []

    for r in results:

        if isinstance(r, AssetSnapshot):

            out.append(r)

    return out

def _history_sync(symbol: str, period: str = "1y") -> Dict[str, float]:

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

async def fetch_history_universal(symbol: str, period: str = "1y") -> Dict[str, float]:

    ck = f"uhist:{symbol.upper()}:{period}"

    cached = cache.get(ck)

    if cached:

        return cached

    series = await asyncio.to_thread(_history_sync, symbol, period)

    if series:

        cache.set(ck, series, HIST_TTL)

    return series

def _dividends_sync(symbol: str) -> List[Dict[str, float]]:

    try:

        import yfinance as yf

        import pandas as pd

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

    out: List[Dict[str, float]] = []

    for idx, val in s.items():

        try:

            out.append({"date": idx.strftime("%Y-%m-%d"), "value": float(val)})

        except Exception:

            continue

    return out

async def fetch_dividends(symbol: str) -> List[Dict[str, float]]:

    ck = f"udiv:{symbol.upper()}"

    cached = cache.get(ck)

    if cached:

        return cached

    data = await asyncio.to_thread(_dividends_sync, symbol)

    if data:

        cache.set(ck, data, DIV_TTL)

    return data

