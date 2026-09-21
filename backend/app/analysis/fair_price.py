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

    fair_low: float | None = None

    fair_high: float | None = None

    band_position: float | None = None

    band_quality: str = "sem_faixa"

    independent_inputs: int = 0

    methods: list[dict] = field(default_factory=list)

    method_dispersion: float | None = None

    methods_disagree: bool = False

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
    reference: datetime | None = None,
) -> float | None:
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

    return sum(values) / len(values)


DIVIDEND_OUTLIER_RATIO = 3.0

MIN_YEARS_FOR_OUTLIER = 3


def normalized_annual_dividend(
    dividends: list[dict[str, float]],
    years: int = DIVIDEND_WINDOW_YEARS,
    reference: datetime | None = None,
) -> tuple[float | None, bool]:
    today = reference or _now()
    by_year = _dividends_by_year(dividends)

    oldest_allowed = today.year - years
    last_complete_year = today.year - 1
    covered = {y: v for y, v in by_year.items() if oldest_allowed <= y <= last_complete_year}
    if not covered:
        return average_dividend_last_12m(dividends, reference=today), False

    values = [covered.get(y, 0.0) for y in range(min(covered), last_complete_year + 1)]
    media = sum(values) / len(values)

    if len(values) < MIN_YEARS_FOR_OUTLIER:
        return media, False

    ordenados = sorted(values)
    meio = len(ordenados) // 2
    mediana = ordenados[meio] if len(ordenados) % 2 else (ordenados[meio - 1] + ordenados[meio]) / 2

    if mediana <= 0 or max(values) <= mediana * DIVIDEND_OUTLIER_RATIO:
        return media, False

    return mediana, True


def dividend_data_years(
    dividends: list[dict[str, float]],
    years: int = DIVIDEND_WINDOW_YEARS,
    reference: datetime | None = None,
) -> int:
    today = reference or _now()
    by_year = _dividends_by_year(dividends)
    return len([y for y in by_year if today.year - years <= y <= today.year])


def bazin_fair_price(
    avg_dividend: float | None, desired_yield: float = DEFAULT_DESIRED_YIELD
) -> float | None:

    if not avg_dividend or avg_dividend <= 0 or desired_yield <= 0:
        return None

    return round(avg_dividend / desired_yield, 2)


METHOD_INPUT = {
    "bazin": "dividendo",
    "graham": "lucro",
    "dcf": "lucro",
    "vpa": "patrimonio",
}

METHODS_BY_TYPE = {
    "fii": ("bazin", "vpa"),
    "etf": (),
    "bdr": ("graham", "dcf"),
}

BAND_OUTLIER_RATIO = 2.0


def _method_status(nome: str, inputs: FairPriceInputs, valor: float | None) -> dict:
    aplicaveis = METHODS_BY_TYPE.get(inputs.asset_type, ("bazin", "graham", "dcf"))
    estado, nota = "ok", ""

    if nome not in aplicaveis:
        estado, nota = "inaplicavel", "o método não descreve esta classe de ativo"
    elif valor is not None:
        estado = "ok"
    elif nome == "bazin":
        estado, nota = "sem_dado", "sem histórico de dividendo no período"
    elif nome == "vpa":
        estado, nota = "sem_dado", "sem valor patrimonial informado"
    elif inputs.eps is None:
        estado, nota = "sem_dado", "lucro por ação não informado"
    elif inputs.eps <= 0:
        estado, nota = "lucro_negativo", "a empresa não teve lucro no período"
    elif nome == "graham" and (inputs.book_value is None or inputs.book_value <= 0):
        estado, nota = "sem_dado", "sem valor patrimonial positivo"
    elif nome == "graham":
        estado, nota = "fora_da_faixa", "P/L acima de 15 ou P/VP acima de 1,5"
    else:
        estado, nota = "sem_dado", "insumo ausente"

    return {
        "method": nome,
        "input": METHOD_INPUT[nome],
        "value": valor,
        "status": estado,
        "note": nota,
    }


def _band_from(candidatos: dict[str, float]) -> tuple[float | None, float | None, str | None]:
    if not candidatos:
        return None, None, None

    valores = sorted(candidatos.values())
    fora: str | None = None

    if len(valores) >= 3:
        meio = len(valores) // 2
        mediana = valores[meio] if len(valores) % 2 else (valores[meio - 1] + valores[meio]) / 2
        if mediana > 0:
            for nome, valor in candidatos.items():
                if valor > mediana * BAND_OUTLIER_RATIO or valor * BAND_OUTLIER_RATIO < mediana:
                    fora = nome
                    break

    return round(min(valores), 2), round(max(valores), 2), fora


def band_position(
    price: float | None, fair_low: float | None, fair_high: float | None
) -> float | None:
    if not price or fair_low is None or fair_high is None:
        return None
    if not (fair_low <= price <= fair_high):
        return None
    if fair_high == fair_low:
        return 0.5
    return round((price - fair_low) / (fair_high - fair_low), 4)


def margin_of_safety_in_band(
    price: float | None,
    fair_low: float | None,
    fair_high: float | None,
) -> float | None:
    if not price or price <= 0 or fair_low is None or fair_high is None:
        return None

    if price < fair_low:
        return round((fair_low - price) / fair_low, 4)

    if price > fair_high:
        return round((fair_high - price) / fair_high, 4)

    return 0.0


GRAHAM_MAX_PE = 15.0
GRAHAM_MAX_PB = 1.5

MAX_METHOD_DISPERSION = 2.0


def graham_fair_price(
    eps: float | None,
    book_value: float | None,
    price: float | None = None,
    pb_ratio: float | None = None,
) -> float | None:
    if eps is None or book_value is None or eps <= 0 or book_value <= 0:
        return None

    if price is not None and price > 0:
        if price / eps > GRAHAM_MAX_PE:
            return None

        pb = pb_ratio if (pb_ratio and pb_ratio > 0) else price / book_value
        if pb > GRAHAM_MAX_PB:
            return None

    return round(math.sqrt(22.5 * eps * book_value), 2)


DCF_DEFAULT_GROWTH_PCT = 8.0
DCF_MAX_GROWTH_PCT = 25.0

DCF_FALLBACK_DISCOUNT = 0.13

EQUITY_RISK_PREMIUM = 0.05


def discount_rate_from(selic_anual_pct: float | None) -> float:
    if not selic_anual_pct or selic_anual_pct <= 0:
        return DCF_FALLBACK_DISCOUNT
    return round(selic_anual_pct / 100 + EQUITY_RISK_PREMIUM, 4)


def dcf_fair_price(
    eps: float | None,
    revenue_growth_pct: float | None = None,
    discount_rate: float = DCF_FALLBACK_DISCOUNT,
    growth_years: int = 5,
    terminal_pe: float = 15.0,
) -> float | None:
    if eps is None or eps <= 0:
        return None

    growth_pct = DCF_DEFAULT_GROWTH_PCT
    if revenue_growth_pct is not None:
        growth_pct = max(0.0, min(revenue_growth_pct, DCF_MAX_GROWTH_PCT))

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
    discount_rate: float = DCF_FALLBACK_DISCOUNT
    dcf_sem_crescimento: float | None = None
    growth_source: str = "ausente"

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
    discount_rate: float | None = None,
) -> FairPriceInputs:
    is_fii = asset_type == "fii"
    is_etf = asset_type == "etf"

    today = reference or _now()

    avg_div, used_median = normalized_annual_dividend(dividends, reference=today)

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
    dcf_sem_crescimento: float | None = None
    if not is_fii and not is_etf:
        graham = graham_fair_price(eps, book_value, price=price, pb_ratio=pb_ratio)
        if eps is not None and eps > 0:
            taxa = discount_rate or DCF_FALLBACK_DISCOUNT
            dcf = dcf_fair_price(eps, revenue_growth_pct, discount_rate=taxa)
            dcf_sem_crescimento = dcf_fair_price(eps, 0.0, discount_rate=taxa)

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
        discount_rate=discount_rate or DCF_FALLBACK_DISCOUNT,
        dcf_sem_crescimento=dcf_sem_crescimento,
        growth_source=(
            "ausente"
            if revenue_growth_pct is None
            else "contracao"
            if revenue_growth_pct < 0
            else "estagnacao"
            if revenue_growth_pct == 0
            else "medido"
        ),
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
        candidatos = {"bazin": bazin, "vpa": inputs.pvp_fair}
    elif is_etf:
        bazin = None
        candidatos = {}
    elif is_bdr:
        bazin = None
        candidatos = {"graham": graham, "dcf": dcf}
    else:
        candidatos = {"bazin": bazin, "graham": graham, "dcf": dcf}

    validos = {n: v for n, v in candidatos.items() if v is not None}
    fair_low, fair_high, destoante = _band_from(validos)
    usados = validos

    consensus = round(sum(usados.values()) / len(usados), 2) if usados else None
    consensus_methods = len(usados)

    independent_inputs = len({METHOD_INPUT[n] for n in usados})

    dispersion: float | None = None
    if len(usados) >= 2:
        menor = min(usados.values())
        if menor > 0:
            dispersion = round(max(usados.values()) / menor, 2)
    disagree = dispersion is not None and dispersion >= MAX_METHOD_DISPERSION

    if fair_low is None:
        band_quality = "sem_faixa"
    elif independent_inputs <= 1:
        band_quality = "fragil"
    elif destoante or disagree:
        band_quality = "ampla"
    else:
        band_quality = "firme"

    diagnostico = [
        _method_status(nome, inputs, validos.get(nome))
        for nome in ("bazin", "graham", "dcf", "vpa")
    ]
    if destoante:
        for item in diagnostico:
            if item["method"] == destoante:
                item["status"] = "destoa_dos_demais"
                item["note"] = (
                    "afasta-se mais de 2x da mediana dos outros: é ele que alarga a faixa"
                )

    mos = margin_of_safety_in_band(price, fair_low, fair_high)

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
        method_dispersion=dispersion,
        methods_disagree=disagree,
        margin_of_safety=mos,
        fair_low=fair_low,
        fair_high=fair_high,
        band_position=band_position(price, fair_low, fair_high),
        band_quality=band_quality,
        independent_inputs=independent_inputs,
        methods=diagnostico,
        avg_dividend_5y=round(inputs.avg_dividend, 4) if inputs.avg_dividend else None,
        dy_12m=dy_12m,
        dy_5y=dy_5y,
        data_years=inputs.data_years,
        desired_yield_used=effective_yield,
        pvp=inputs.pvp,
        details={
            "discount_rate_pct": round(inputs.discount_rate * 100, 2),
            "dcf_sem_crescimento": inputs.dcf_sem_crescimento,
            "growth_source": inputs.growth_source,
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
    discount_rate: float | None = None,
) -> FairPriceResult:
    inputs = compute_fair_price_inputs(
        price=price,
        eps=eps,
        book_value=book_value,
        dividends=dividends,
        asset_type=asset_type,
        revenue_growth_pct=revenue_growth_rate,
        pb_ratio=pb_ratio,
        reference=reference,
        discount_rate=discount_rate,
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

    range_52w_position: float | None = None

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

    posicao_52s = None
    if last and week52_high and week52_low and week52_high > week52_low:
        posicao_52s = round((last - week52_low) / (week52_high - week52_low), 4)
        posicao_52s = min(1.0, max(0.0, posicao_52s))

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
        range_52w_position=posicao_52s,
    )
