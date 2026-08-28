from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx

from app.collectors import circuit, plausibility
from app.core import cache
from app.core.config import get_settings
from app.core.observability import record_external_call
from app.core.universe import KNOWN_ETFS, get_sector_map
from app.models.enums import AssetType

logger = logging.getLogger(__name__)


class UnsupportedTickerError(ValueError):
    """Ticker não corresponde a nenhum asset_type suportado (br_stock/bdr/fii/etf)."""


FUND_TTL = 2 * 3600
HIST_TTL = 12 * 3600
DIV_TTL = 24 * 3600

_FETCH_SEMAPHORE = asyncio.Semaphore(30)

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

_ROOT = r"[A-Z][A-Z0-9]{3}"
_BDR = re.compile(rf"^{_ROOT}3\d$")
_ENDS_11 = re.compile(rf"^{_ROOT}11$")
_BR_STOCK = re.compile(rf"^{_ROOT}\d{{1,2}}$")

_BRAPI_BASE = "https://brapi.dev/api"


def detect_type(symbol: str) -> AssetType:
    s = symbol.strip().upper()
    base = s[:-3] if s.endswith(".SA") else s

    if base in KNOWN_ETFS:
        return AssetType.etf

    if _BDR.match(base):
        return AssetType.bdr

    if _ENDS_11.match(base):
        return AssetType.br_stock if base in KNOWN_UNITS else AssetType.fii

    if _BR_STOCK.match(base):
        return AssetType.br_stock

    raise UnsupportedTickerError(
        f"Tipo de ativo não suportado para {symbol!r} — este sistema cobre apenas "
        "ações BR, BDRs, FIIs e ETFs da B3."
    )


def _base_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if s.endswith(".SA"):
        return s[:-3]
    if "-USD" in s or "-BRL" in s:
        return s.split("-")[0]
    return s


@dataclass
class AssetSnapshot:
    symbol: str
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

    as_of: float = 0.0
    source: str = "brapi"

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def _safe_float(v) -> float | None:
    try:
        return float(v) if v is not None else None
    except (ValueError, TypeError):
        return None


def _ratio_to_pct(v) -> float | None:
    """Converte razão decimal da BRAPI para percentual (0.2039 -> 20.39)."""
    try:
        if v is None:
            return None
        return round(float(v) * 100.0, 4)
    except (ValueError, TypeError):
        return None


def _cash_dividends(raw: dict) -> list[dict]:
    return (raw.get("dividendsData") or {}).get("cashDividends") or []


def _dividend_date(d: dict) -> str | None:
    raw_date = d.get("paymentDate") or d.get("approvedOn")
    return str(raw_date)[:10] if raw_date else None


def _sum_dividends_last_12m(raw: dict, reference: datetime | None = None) -> float:
    """Soma os proventos dos últimos 12 meses **por data de pagamento**."""
    today = reference or datetime.now(UTC)
    cutoff = (today - timedelta(days=365)).strftime("%Y-%m-%d")
    horizon = today.strftime("%Y-%m-%d")

    total = 0.0
    for d in _cash_dividends(raw):
        date_str = _dividend_date(d)
        if date_str is None or date_str < cutoff or date_str > horizon:
            continue
        total += _safe_float(d.get("rate")) or 0.0
    return total


def _calculate_dividend_yield(dividends_12m: float, current_price: float) -> float | None:
    try:
        if current_price <= 0 or dividends_12m < 0:
            return None
        return round((dividends_12m / current_price) * 100, 2)
    except (ValueError, TypeError, ZeroDivisionError):
        return None


_BRAPI_RAW_TTL = FUND_TTL


_FALLBACK_HISTORY_RANGE = "3mo"


_BRAPI_PROVIDER = "brapi"


def _brapi_raw(base: str) -> dict:
    ck = f"brapi_raw:{base}"
    cached = cache.get(ck)
    if cached is not None:
        return cached

    # Fonte fora do ar: nem tenta. Esperar o timeout em cada requisição de
    # usuário deixa o app lento em vez de honesto — e quem chama aqui cai no
    # cache vencido, que é dado antigo mas é dado, com a idade visível na tela.
    if not circuit.allows(_BRAPI_PROVIDER):
        return {}

    settings = get_settings()
    ranges = [settings.brapi_history_range]
    if _FALLBACK_HISTORY_RANGE not in ranges:
        ranges.append(_FALLBACK_HISTORY_RANGE)

    r: dict | None = None
    for range_param in ranges:
        try:
            resp = httpx.get(
                f"{_BRAPI_BASE}/quote/{base}",
                params={
                    "token": settings.brapi_token,
                    "fundamental": "true",
                    "range": range_param,
                    "interval": "1d",
                },
                timeout=15,
            )
            resp.raise_for_status()
            record_external_call("brapi", ok=True)
            circuit.record_success(_BRAPI_PROVIDER)
            results = resp.json().get("results") or []
            if not results:
                return {}
            r = results[0]
            break
        except httpx.HTTPStatusError as e:
            record_external_call("brapi", ok=False)
            # 400 por range é limitação do plano, não fonte fora do ar: o
            # disjuntor não deve abrir por isso, senão o plano gratuito
            # derrubaria a integração inteira.
            if e.response.status_code == 400 and range_param != ranges[-1]:
                logger.info(
                    "brapi rejeitou range=%s para %s; degradando para %s",
                    range_param,
                    base,
                    _FALLBACK_HISTORY_RANGE,
                )
                continue
            circuit.record_failure(_BRAPI_PROVIDER, f"HTTP {e.response.status_code}")
            logger.warning("brapi falhou %s: %s", base, e)
            return {}
        except Exception as e:
            record_external_call("brapi", ok=False)
            circuit.record_failure(_BRAPI_PROVIDER, type(e).__name__)
            logger.warning("brapi falhou %s: %s", base, e)
            return {}

    if r is None:
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
    try:
        total_12m = _sum_dividends_last_12m(r)
        if total_12m > 0:
            dividend_yield = _calculate_dividend_yield(total_12m, price)
    except Exception:
        logger.debug("Falha ao calcular DY de %s", base, exc_info=True)

    sector = r.get("sector") or get_sector_map().get(base)

    numeros = {
        "price": price,
        "market_cap": _safe_float(r.get("marketCap")),
        "pe_ratio": _safe_float(r.get("priceEarnings")),
        "pb_ratio": _safe_float(r.get("priceToBook") or r.get("pvp")),
        "eps": _safe_float(r.get("earningsPerShare")),
        "book_value": _safe_float(r.get("bookValue")),
        "roe": _ratio_to_pct(r.get("returnOnEquity")),
        "dividend_yield": dividend_yield,
        "debt_to_equity": _ratio_to_pct(r.get("debtToEquity")),
        "profit_margin": _ratio_to_pct(r.get("profitMargins")),
        "revenue_growth": _ratio_to_pct(r.get("revenueGrowth")),
        "fifty_two_week_high": _safe_float(r.get("fiftyTwoWeekHigh")),
        "fifty_two_week_low": _safe_float(r.get("fiftyTwoWeekLow")),
    }

    # Validação por magnitude, e não só por tipo: um ROE de 12.000% ou um preço
    # de R$ 0,0001 passam pelo `float()` e viram veredito. Campo implausível é
    # zerado — o produto sabe conviver com indicador ausente; preço implausível
    # rejeita o snapshot inteiro, porque sem preço não há tela nenhuma.
    numeros, veredito = plausibility.screen(numeros, symbol=symbol.upper())
    if not veredito.accepted:
        record_external_call("brapi.plausibility", ok=False)
        return None

    return AssetSnapshot(
        symbol=symbol.upper(),
        as_of=time.time(),
        source="brapi",
        asset_type=t,
        name=name,
        sector=sector,
        currency=r.get("currency") or "BRL",
        **numeros,
    )


def _history_brapi(symbol: str, period: str = "1y") -> dict[str, float]:
    base = _base_symbol(symbol)
    r = _brapi_raw(base)
    prices = r.get("historicalDataPrice") or []

    days_map = {
        "1d": 1,
        "5d": 5,
        "1mo": 31,
        "3mo": 92,
        "6mo": 182,
        "1y": 365,
        "2y": 730,
        "max": 10_000,
    }
    max_days = days_map.get(period, 365)
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

    out: list[dict[str, float]] = []
    for d in _cash_dividends(r):
        date = _dividend_date(d)
        value = _safe_float(d.get("rate"))
        if date and value is not None:
            out.append({"date": date, "value": value})
    return sorted(out, key=lambda x: x["date"])


def _fetch_sync(symbol: str, asset_type: AssetType | None = None) -> AssetSnapshot | None:
    t = asset_type or detect_type(symbol)

    if t in ("br_stock", "fii", "bdr", "etf"):
        return _fetch_brapi(symbol, t)
    return None


def _history_sync(symbol: str, period: str = "1y") -> dict[str, float]:
    t = detect_type(symbol)

    if t in ("br_stock", "fii", "bdr", "etf"):
        return _history_brapi(symbol, period)
    return {}


def _dividends_sync(symbol: str) -> list[dict[str, float]]:
    t = detect_type(symbol)

    if t in ("br_stock", "fii", "bdr", "etf"):
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


_IBOV_SYMBOL = "^BVSP"


def _fetch_ibov_history_sync(days: int) -> dict[str, float]:
    settings = get_settings()
    range_param = "1y" if days > 90 else "3mo"
    try:
        resp = httpx.get(
            f"{_BRAPI_BASE}/quote/{_IBOV_SYMBOL}",
            params={
                "token": settings.brapi_token,
                "range": range_param,
                "interval": "1d",
            },
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json().get("results") or []
        if not results:
            return {}
        prices = results[0].get("historicalDataPrice") or []
    except Exception as e:
        logger.warning("brapi falhou ao buscar histórico do Ibovespa: %s", e)
        return {}

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


async def fetch_ibov_history(days: int = 365) -> dict[str, float]:
    """Histórico diário do Ibovespa (fechamento por dia, YYYY-MM-DD)."""
    ck = f"uhist:{_IBOV_SYMBOL}:{days}"
    cached = cache.get(ck)
    if cached is not None:
        return cached

    series = await asyncio.to_thread(_fetch_ibov_history_sync, days)
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
