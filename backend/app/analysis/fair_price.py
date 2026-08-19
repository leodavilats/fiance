from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime

DESIRED_YIELD_STOCK = 0.06
DESIRED_YIELD_FII = 0.10
DESIRED_YIELD_BDR = 0.04
DESIRED_YIELD_ETF = 0.04
DEFAULT_DESIRED_YIELD = DESIRED_YIELD_STOCK


def desired_yield_for(asset_type: str, prefs: dict | None = None) -> float:
    stock = DESIRED_YIELD_STOCK
    fii = DESIRED_YIELD_FII
    bdr = DESIRED_YIELD_BDR
    etf = DESIRED_YIELD_ETF
    if prefs:
        stock = prefs.get("desired_yield_stock") or stock
        fii = prefs.get("desired_yield_fii") or fii
        bdr = prefs.get("desired_yield_bdr") or bdr
        etf = prefs.get("desired_yield_etf") or etf

    if asset_type == "fii":
        return fii
    if asset_type == "bdr":
        return bdr
    if asset_type == "etf":
        return etf
    return stock


@dataclass
class FairPriceResult:
    bazin: float | None

    graham: float | None

    dcf: float | None

    consensus: float | None

    consensus_methods: int

    margin_of_safety: float | None

    avg_dividend_5y: float | None

    dy_12m: float | None

    dy_5y: float | None

    data_years: int

    desired_yield_used: float

    pvp: float | None = None

    details: dict[str, float | None] = field(default_factory=dict)


def average_dividend_last_12m(
    dividends: list[dict[str, float]],
) -> float | None:
    if not dividends:
        return None

    today = datetime.utcnow()
    cutoff_str = f"{today.year - 1}-{today.month:02d}-{today.day:02d}"

    total = 0.0
    found = False
    for d in dividends:
        try:
            date_str = d["date"][:10]
        except Exception:
            continue
        if date_str >= cutoff_str:
            total += float(d.get("value", 0.0))
            found = True

    return round(total, 4) if found else None


def average_dividend_last_n_years(
    dividends: list[dict[str, float]], years: int = 5, use_median: bool = False
) -> float | None:

    if not dividends:
        return None

    today = datetime.utcnow()

    by_year: dict[int, float] = {}

    cutoff = today.year - years

    for d in dividends:
        try:
            y = int(d["date"][:4])

        except Exception:
            continue

        if y <= cutoff or y > today.year:
            continue

        by_year[y] = by_year.get(y, 0.0) + float(d.get("value", 0.0))

    if not by_year:
        return None

    values = list(by_year.values())

    if use_median:
        values_sorted = sorted(values)

        n = len(values_sorted)

        if n % 2 == 0:
            return (values_sorted[n // 2 - 1] + values_sorted[n // 2]) / 2

        else:
            return values_sorted[n // 2]

    else:
        return sum(values) / years


def bazin_fair_price(
    avg_dividend: float | None, desired_yield: float = DEFAULT_DESIRED_YIELD
) -> float | None:

    if not avg_dividend or avg_dividend <= 0 or desired_yield <= 0:
        return None

    return round(avg_dividend / desired_yield, 2)


def graham_fair_price(eps: float | None, book_value: float | None) -> float | None:

    if eps is None or book_value is None or eps <= 0 or book_value <= 0:
        return None

    return round(math.sqrt(22.5 * eps * book_value), 2)


def dcf_fair_price(
    eps: float | None,
    revenue_growth_rate: float | None = None,
    discount_rate: float = 0.13,
    growth_years: int = 5,
    terminal_pe: float = 15.0,
) -> float | None:
    if eps is None or eps <= 0:
        return None

    growth = (
        revenue_growth_rate
        if (revenue_growth_rate is not None and 0 < revenue_growth_rate < 1)
        else 0.08
    )

    pv_earnings = 0.0
    current_eps = eps
    for year in range(1, growth_years + 1):
        projected_eps = current_eps * (1 + growth) ** year
        pv_earnings += projected_eps / (1 + discount_rate) ** year

    terminal_eps = eps * (1 + growth) ** growth_years
    terminal_value = terminal_eps * terminal_pe / (1 + discount_rate) ** growth_years

    fair = pv_earnings + terminal_value
    return round(fair, 2) if fair > 0 else None


def compute_fair_price(
    price: float | None,
    eps: float | None,
    book_value: float | None,
    dividends: list[dict[str, float]],
    asset_type: str = "br_stock",
    week52_high: float | None = None,
    desired_yield: float | None = None,
    revenue_growth_rate: float | None = None,
    pb_ratio: float | None = None,
) -> FairPriceResult:

    is_fii = asset_type == "fii"
    is_etf = asset_type == "etf"
    is_bdr = asset_type == "bdr"

    if desired_yield and desired_yield > 0:
        effective_yield = desired_yield
    elif is_fii:
        effective_yield = DESIRED_YIELD_FII
    elif is_etf:
        effective_yield = DESIRED_YIELD_ETF
    elif is_bdr:
        effective_yield = DESIRED_YIELD_BDR
    else:
        effective_yield = DESIRED_YIELD_STOCK

    today = datetime.utcnow()
    years_with_data: set[int] = set()
    for d in dividends:
        try:
            y = int(d["date"][:4])
        except Exception:
            continue
        if y <= today.year and y > today.year - 6:
            years_with_data.add(y)
    data_years = len(years_with_data)

    avg_div = average_dividend_last_n_years(dividends, years=5, use_median=False)
    use_median = False

    if avg_div and price and price > 0:
        implied_dy = avg_div / price
        if implied_dy > 0.30:
            avg_div = average_dividend_last_n_years(dividends, years=5, use_median=True)
            use_median = True

    bazin = bazin_fair_price(avg_div, effective_yield)

    pvp: float | None = None
    pvp_fair: float | None = None
    if book_value and book_value > 0:
        if pb_ratio and pb_ratio > 0:
            pvp = round(pb_ratio, 2)
        elif price and price > 0:
            pvp = round(price / book_value, 2)
        pvp_fair = round(book_value, 2)

    graham: float | None = None
    dcf: float | None = None

    if is_fii:
        candidates = [v for v in (bazin, pvp_fair) if v is not None]
    elif is_etf:
        # ETF é cota de fundo, sem EPS/book_value de empresa — Graham/DCF não
        # se aplicam; fair price fica só no dividend yield histórico (Bazin).
        candidates = [v for v in (bazin,) if v is not None]
    elif is_bdr:
        bazin = None
        graham = graham_fair_price(eps, book_value)
        if eps is not None and eps > 0:
            dcf = dcf_fair_price(eps, revenue_growth_rate)
        candidates = [v for v in (graham, dcf) if v is not None]
    else:
        graham = graham_fair_price(eps, book_value)
        if eps is not None and eps > 0 and bazin is None:
            dcf = dcf_fair_price(eps, revenue_growth_rate)
        candidates = [v for v in (bazin, graham, dcf) if v is not None]

    consensus = round(sum(candidates) / len(candidates), 2) if candidates else None
    consensus_methods = len(candidates)

    mos = None

    if consensus and price and price > 0:
        mos = round((consensus - price) / consensus, 4)

    div_12m = average_dividend_last_12m(dividends)
    dy_12m = round(div_12m / price, 4) if (div_12m is not None and price and price > 0) else None

    dy_5y = round(avg_div / price, 4) if (avg_div is not None and price and price > 0) else None

    return FairPriceResult(
        bazin=bazin,
        graham=graham,
        dcf=dcf,
        consensus=consensus,
        consensus_methods=consensus_methods,
        margin_of_safety=mos,
        avg_dividend_5y=round(avg_div, 4) if avg_div else None,
        dy_12m=dy_12m,
        dy_5y=dy_5y,
        data_years=data_years,
        desired_yield_used=effective_yield,
        pvp=pvp,
        details={
            "eps": eps,
            "book_value": book_value,
            "desired_yield_pct": effective_yield * 100,
            "used_median": use_median,
            "pvp_fair": pvp_fair,
        },
    )


@dataclass
class TechnicalSnapshot:
    sma_50: float | None

    sma_200: float | None

    rsi_14: float | None

    trend: str

    last_price: float | None

    distance_from_52w_high_pct: float | None

    distance_from_52w_low_pct: float | None


def _series_from_history(history: dict[str, float]) -> list[tuple[str, float]]:

    return sorted(history.items(), key=lambda kv: kv[0])


def sma(values: list[float], window: int) -> float | None:

    if len(values) < window:
        return None

    return round(sum(values[-window:]) / window, 4)


def rsi(values: list[float], period: int = 14) -> float | None:

    if len(values) < period + 1:
        return None

    gains = 0.0

    losses = 0.0

    for i in range(-period, 0):
        diff = values[i] - values[i - 1]

        if diff >= 0:
            gains += diff

        else:
            losses -= diff

    if losses == 0:
        return 100.0

    rs = (gains / period) / (losses / period)

    return round(100 - (100 / (1 + rs)), 2)


def compute_technical(
    history: dict[str, float],
    week52_high: float | None = None,
    week52_low: float | None = None,
) -> TechnicalSnapshot:

    series = _series_from_history(history)

    closes = [v for _, v in series]

    last = closes[-1] if closes else None

    s50 = sma(closes, 50)

    s200 = sma(closes, 200)

    r14 = rsi(closes, 14)

    trend = "unknown"

    if s50 and s200:
        if s50 > s200 * 1.01:
            trend = "uptrend"

        elif s50 < s200 * 0.99:
            trend = "downtrend"

        else:
            trend = "sideways"

    d_high = None

    d_low = None

    if last and week52_high and week52_high > 0:
        d_high = round((last - week52_high) / week52_high * 100, 2)

    if last and week52_low and week52_low > 0:
        d_low = round((last - week52_low) / week52_low * 100, 2)

    return TechnicalSnapshot(
        sma_50=s50,
        sma_200=s200,
        rsi_14=r14,
        trend=trend,
        last_price=last,
        distance_from_52w_high_pct=d_high,
        distance_from_52w_low_pct=d_low,
    )
