from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

DEFAULT_DESIRED_YIELD = 0.06


@dataclass
class FairPriceResult:
    bazin: float | None

    graham: float | None

    consensus: float | None

    margin_of_safety: float | None

    avg_dividend_5y: float | None

    details: dict[str, float | None]


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


def compute_fair_price(
    price: float | None,
    eps: float | None,
    book_value: float | None,
    dividends: list[dict[str, float]],
    desired_yield: float = DEFAULT_DESIRED_YIELD,
    week52_high: float | None = None,
) -> FairPriceResult:

    avg_div = average_dividend_last_n_years(dividends, years=5, use_median=False)
    use_median = False

    if avg_div and price and price > 0:
        implied_dy = avg_div / price
        if implied_dy > 0.30:
            avg_div = average_dividend_last_n_years(dividends, years=5, use_median=True)
            use_median = True

    bazin = bazin_fair_price(avg_div, desired_yield)
    graham = graham_fair_price(eps, book_value)

    candidates = [v for v in (bazin, graham) if v is not None]

    consensus = round(sum(candidates) / len(candidates), 2) if candidates else None

    mos = None

    if consensus and price and price > 0:
        mos = round((consensus - price) / consensus, 4)

    return FairPriceResult(
        bazin=bazin,
        graham=graham,
        consensus=consensus,
        margin_of_safety=mos,
        avg_dividend_5y=round(avg_div, 4) if avg_div else None,
        details={
            "eps": eps,
            "book_value": book_value,
            "desired_yield_pct": desired_yield * 100,
            "used_median": use_median,
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
