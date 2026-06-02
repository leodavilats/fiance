from __future__ import annotations

import asyncio
import logging

from alpha_vantage.fundamentaldata import FundamentalData
from alpha_vantage.timeseries import TimeSeries

from app.core import cache
from app.core.config import get_settings
from app.models.company import CompanyFundamentals

logger = logging.getLogger(__name__)

FUND_TTL = 6 * 3600
HIST_TTL = 12 * 3600


def _safe_float(value, default: float | None = None) -> float | None:
    try:
        if value is None or value == "None" or value == "-":
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def _safe_pct(value) -> float | None:
    try:
        if value is None or value == "None" or value == "-":
            return None
        f = float(value)

        if f > 1:
            return f

        return f * 100
    except (ValueError, TypeError):
        return None


async def _fetch_alpha_overview(ticker: str, api_key: str) -> CompanyFundamentals | None:
    if not api_key:
        logger.debug("Alpha Vantage API key not configured")
        return None

    def _fetch():
        try:
            fd = FundamentalData(key=api_key, output_format="json")
            data, _ = fd.get_company_overview(symbol=ticker)

            if not data or "Symbol" not in data:
                return None

            return CompanyFundamentals(
                ticker=ticker,
                name=data.get("Name"),
                sector=data.get("Sector"),
                price=_safe_float(data.get("LatestQuarter")),
                market_cap=_safe_float(data.get("MarketCapitalization")),
                pe_ratio=_safe_float(data.get("PERatio")),
                pb_ratio=_safe_float(data.get("PriceToBookRatio")),
                roe=_safe_pct(data.get("ReturnOnEquityTTM")),
                dividend_yield=_safe_pct(data.get("DividendYield")),
                debt_to_equity=_safe_float(data.get("DebtToEquity")),
                profit_margin=_safe_pct(data.get("ProfitMargin")),
                revenue_growth=_safe_pct(data.get("QuarterlyRevenueGrowthYOY")),
            )
        except Exception as e:
            logger.warning(f"Alpha Vantage overview failed for {ticker}: {e}")
            return None

    return await asyncio.to_thread(_fetch)


async def _fetch_alpha_quote(ticker: str, api_key: str) -> dict[str, float] | None:
    if not api_key:
        return None

    def _fetch():
        try:
            ts = TimeSeries(key=api_key, output_format="json")
            data, _ = ts.get_quote_endpoint(symbol=ticker)

            if not data or "01. symbol" not in data:
                return None

            return {
                "price": _safe_float(data.get("05. price")),
                "high": _safe_float(data.get("03. high")),
                "low": _safe_float(data.get("04. low")),
                "volume": _safe_float(data.get("06. volume")),
                "change_percent": _safe_float(data.get("10. change percent", "").replace("%", "")),
            }
        except Exception as e:
            logger.warning(f"Alpha Vantage quote failed for {ticker}: {e}")
            return None

    return await asyncio.to_thread(_fetch)


async def fetch_fundamentals(ticker: str) -> CompanyFundamentals | None:
    settings = get_settings()

    cached = cache.get(f"alpha_fund:{ticker}")
    if cached:
        return CompanyFundamentals.model_validate(cached)

    overview = await _fetch_alpha_overview(ticker, settings.alpha_vantage_key)
    if not overview:
        return None

    quote = await _fetch_alpha_quote(ticker, settings.alpha_vantage_key)
    if quote and quote.get("price"):
        overview.price = quote["price"]

    if overview and overview.price:
        cache.set(f"alpha_fund:{ticker}", overview.model_dump(), FUND_TTL)

    return overview


async def fetch_batch_fundamentals(tickers: list[str]) -> list[CompanyFundamentals]:
    tasks = [fetch_fundamentals(ticker) for ticker in tickers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    out: list[CompanyFundamentals] = []
    for ticker, result in zip(tickers, results, strict=False):
        if isinstance(result, Exception):
            logger.warning(f"Error fetching {ticker}: {result}")
            continue
        if result is None:
            logger.info(f"No data for {ticker}")
            continue
        out.append(result)

    return out


async def fetch_historical_prices(ticker: str, outputsize: str = "compact") -> dict | None:
    settings = get_settings()

    cache_key = f"alpha_hist:{ticker}:{outputsize}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    def _fetch():
        try:
            ts = TimeSeries(key=settings.alpha_vantage_key, output_format="json")
            data, _ = ts.get_daily(symbol=ticker, outputsize=outputsize)
            return data
        except Exception as e:
            logger.warning(f"Alpha Vantage historical failed for {ticker}: {e}")
            return None

    data = await asyncio.to_thread(_fetch)

    if data:
        cache.set(cache_key, data, HIST_TTL)

    return data
