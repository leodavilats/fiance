from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import UTC, datetime

DESIRED_YIELD_STOCK = 0.06
DESIRED_YIELD_FII = 0.10
DESIRED_YIELD_BDR = 0.04
DESIRED_YIELD_ETF = 0.04
DEFAULT_DESIRED_YIELD = DESIRED_YIELD_STOCK

DIVIDEND_WINDOW_YEARS = 5

_IMPLIED_DY_OUTLIER = 0.30


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


def _now() -> datetime:
    return datetime.now(UTC)


def _dividends_by_year(dividends: list[dict[str, float]]) -> dict[int, float]:
    by_year: dict[int, float] = {}
    for d in dividends:
        try:
            year = int(str(d["date"])[:4])
        except (KeyError, TypeError, ValueError):
            continue
        try:
            value = float(d.get("value", 0.0))
        except (TypeError, ValueError):
            continue
        by_year[year] = by_year.get(year, 0.0) + value
    return by_year


def average_dividend_last_12m(
    dividends: list[dict[str, float]],
    reference: datetime | None = None,
) -> float | None:
    if not dividends:
        return None

    today = reference or _now()
    cutoff_str = f"{today.year - 1}-{today.month:02d}-{today.day:02d}"
    horizon_str = today.strftime("%Y-%m-%d")

    total = 0.0
    found = False
    for d in dividends:
        try:
            date_str = str(d["date"])[:10]
        except (KeyError, TypeError):
            continue
        if cutoff_str <= date_str <= horizon_str:
            try:
                total += float(d.get("value", 0.0))
            except (TypeError, ValueError):
                continue
            found = True

    return round(total, 4) if found else None


def average_dividend_last_n_years(
    dividends: list[dict[str, float]],
    years: int = DIVIDEND_WINDOW_YEARS,
    use_median: bool = False,
    reference: datetime | None = None,
) -> float | None:
    """Dividendo médio anual sobre anos-calendário **completos**."""
    if not dividends:
        return None

    today = reference or _now()
    by_year = _dividends_by_year(dividends)

    oldest_allowed = today.year - years
    last_complete_year = today.year - 1

    covered = {
        year: value
        for year, value in by_year.items()
        if oldest_allowed <= year <= last_complete_year
    }

    if not covered:
        return average_dividend_last_12m(dividends, reference=today)

    first_year_with_data = min(covered)
    values = [
        covered.get(year, 0.0) for year in range(first_year_with_data, last_complete_year + 1)
    ]

    if use_median:
        values_sorted = sorted(values)
        n = len(values_sorted)
        if n % 2 == 0:
            return (values_sorted[n // 2 - 1] + values_sorted[n // 2]) / 2
        return values_sorted[n // 2]

    return sum(values) / len(values)


def dividend_data_years(
    dividends: list[dict[str, float]],
    years: int = DIVIDEND_WINDOW_YEARS,
    reference: datetime | None = None,
) -> int:
    """Quantos anos-calendário distintos da janela têm provento registrado."""
    today = reference or _now()
    by_year = _dividends_by_year(dividends)
    return len([y for y in by_year if today.year - years <= y <= today.year])


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


DCF_DEFAULT_GROWTH_PCT = 8.0
DCF_MAX_GROWTH_PCT = 25.0


def dcf_fair_price(
    eps: float | None,
    revenue_growth_pct: float | None = None,
    discount_rate: float = 0.13,
    growth_years: int = 5,
    terminal_pe: float = 15.0,
) -> float | None:
    """DCF simplificado sobre o LPA."""
    if eps is None or eps <= 0:
        return None

    growth_pct = DCF_DEFAULT_GROWTH_PCT
    if revenue_growth_pct is not None and 0 < revenue_growth_pct <= DCF_MAX_GROWTH_PCT:
        growth_pct = revenue_growth_pct

    growth = growth_pct / 100.0

    pv_earnings = 0.0
    for year in range(1, growth_years + 1):
        projected_eps = eps * (1 + growth) ** year
        pv_earnings += projected_eps / (1 + discount_rate) ** year

    terminal_eps = eps * (1 + growth) ** growth_years
    terminal_value = terminal_eps * terminal_pe / (1 + discount_rate) ** growth_years

    fair = pv_earnings + terminal_value
    return round(fair, 2) if fair > 0 else None


@dataclass
class FairPriceInputs:
    """Parcela do preço justo que **não** depende das preferências do usuário."""

    asset_type: str
    price: float | None
    eps: float | None
    book_value: float | None
    avg_dividend: float | None
    dividend_12m: float | None
    data_years: int
    graham: float | None
    dcf: float | None
    pvp: float | None
    pvp_fair: float | None
    used_median: bool

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def compute_fair_price_inputs(
    price: float | None,
    eps: float | None,
    book_value: float | None,
    dividends: list[dict[str, float]],
    asset_type: str = "br_stock",
    revenue_growth_pct: float | None = None,
    pb_ratio: float | None = None,
    reference: datetime | None = None,
) -> FairPriceInputs:
    is_fii = asset_type == "fii"
    is_etf = asset_type == "etf"

    today = reference or _now()

    avg_div = average_dividend_last_n_years(dividends, reference=today)
    used_median = False
    if avg_div and price and price > 0 and (avg_div / price) > _IMPLIED_DY_OUTLIER:
        avg_div = average_dividend_last_n_years(dividends, use_median=True, reference=today)
        used_median = True

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
    if not is_fii and not is_etf:
        graham = graham_fair_price(eps, book_value)
        if eps is not None and eps > 0:
            dcf = dcf_fair_price(eps, revenue_growth_pct)

    return FairPriceInputs(
        asset_type=asset_type,
        price=price,
        eps=eps,
        book_value=book_value,
        avg_dividend=round(avg_div, 6) if avg_div else None,
        dividend_12m=average_dividend_last_12m(dividends, reference=today),
        data_years=dividend_data_years(dividends, reference=today),
        graham=graham,
        dcf=dcf,
        pvp=pvp,
        pvp_fair=pvp_fair,
        used_median=used_median,
    )


def fair_price_from_inputs(
    inputs: FairPriceInputs,
    desired_yield: float | None = None,
) -> FairPriceResult:
    asset_type = inputs.asset_type
    is_fii = asset_type == "fii"
    is_etf = asset_type == "etf"
    is_bdr = asset_type == "bdr"

    if desired_yield and desired_yield > 0:
        effective_yield = desired_yield
    else:
        effective_yield = desired_yield_for(asset_type)

    price = inputs.price
    bazin = bazin_fair_price(inputs.avg_dividend, effective_yield)
    graham = inputs.graham
    dcf = inputs.dcf

    if is_fii:
        candidates = [v for v in (bazin, inputs.pvp_fair) if v is not None]
    elif is_etf:
        candidates = [v for v in (bazin,) if v is not None]
    elif is_bdr:
        bazin = None
        candidates = [v for v in (graham, dcf) if v is not None]
    else:
        if bazin is not None:
            dcf = None
        candidates = [v for v in (bazin, graham, dcf) if v is not None]

    consensus = round(sum(candidates) / len(candidates), 2) if candidates else None
    consensus_methods = len(candidates)

    mos = None
    if consensus and price and price > 0:
        mos = round((consensus - price) / consensus, 4)

    dy_12m = (
        round(inputs.dividend_12m / price, 4)
        if (inputs.dividend_12m is not None and price and price > 0)
        else None
    )
    dy_5y = (
        round(inputs.avg_dividend / price, 4)
        if (inputs.avg_dividend is not None and price and price > 0)
        else None
    )

    return FairPriceResult(
        bazin=bazin,
        graham=graham,
        dcf=dcf,
        consensus=consensus,
        consensus_methods=consensus_methods,
        margin_of_safety=mos,
        avg_dividend_5y=round(inputs.avg_dividend, 4) if inputs.avg_dividend else None,
        dy_12m=dy_12m,
        dy_5y=dy_5y,
        data_years=inputs.data_years,
        desired_yield_used=effective_yield,
        pvp=inputs.pvp,
        details={
            "eps": inputs.eps,
            "book_value": inputs.book_value,
            "desired_yield_pct": effective_yield * 100,
            "used_median": inputs.used_median,
            "pvp_fair": inputs.pvp_fair,
        },
    )


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
    reference: datetime | None = None,
) -> FairPriceResult:
    """Atalho de uma chamada: monta os inputs e aplica o desired_yield."""
    inputs = compute_fair_price_inputs(
        price=price,
        eps=eps,
        book_value=book_value,
        dividends=dividends,
        asset_type=asset_type,
        revenue_growth_pct=revenue_growth_rate,
        pb_ratio=pb_ratio,
        reference=reference,
    )
    return fair_price_from_inputs(inputs, desired_yield=desired_yield)


TREND_BASIS_LONG = "long"
TREND_BASIS_SHORT = "short"
TREND_BASIS_NONE = "none"


@dataclass
class TechnicalSnapshot:
    sma_50: float | None

    sma_200: float | None

    rsi_14: float | None

    trend: str

    last_price: float | None

    distance_from_52w_high_pct: float | None

    distance_from_52w_low_pct: float | None

    sma_20: float | None = None

    trend_basis: str = TREND_BASIS_NONE

    data_points: int = 0

    def to_dict(self) -> dict:
        return self.__dict__.copy()


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


def _classify_trend(fast: float, slow: float) -> str:
    if fast > slow * 1.01:
        return "uptrend"
    if fast < slow * 0.99:
        return "downtrend"
    return "sideways"


def compute_technical(
    history: dict[str, float],
    week52_high: float | None = None,
    week52_low: float | None = None,
) -> TechnicalSnapshot:

    series = _series_from_history(history)

    closes = [v for _, v in series]

    last = closes[-1] if closes else None

    s20 = sma(closes, 20)
    s50 = sma(closes, 50)
    s200 = sma(closes, 200)

    r14 = rsi(closes, 14)

    trend = "unknown"
    trend_basis = TREND_BASIS_NONE

    if s50 and s200:
        trend = _classify_trend(s50, s200)
        trend_basis = TREND_BASIS_LONG
    elif s20 and s50:
        trend = _classify_trend(s20, s50)
        trend_basis = TREND_BASIS_SHORT

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
        sma_20=s20,
        trend_basis=trend_basis,
        data_points=len(closes),
    )
