from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime

from app.core.brt import BRT, now_brt

DESIRED_YIELD_STOCK = 0.06
DESIRED_YIELD_FII = 0.10
DESIRED_YIELD_BDR = 0.04
DESIRED_YIELD_ETF = 0.04
DEFAULT_DESIRED_YIELD = DESIRED_YIELD_STOCK

DIVIDEND_WINDOW_YEARS = 5
MIN_DIVIDEND_YEARS = 3
DIVIDEND_CAP_RATIO = 2.0
DIVIDEND_CUT_RATIO = 0.5
LOW_PAYOUT = 0.25

EARNINGS_YEARS = 3
UNSTABLE_EARNINGS_RATIO = 2.0

INFLATION_TARGET = 0.03
LONG_RUN_REAL_GROWTH = 0.015
EQUITY_RISK_PREMIUM = 0.05
LONG_RUN_GROWTH = INFLATION_TARGET + LONG_RUN_REAL_GROWTH
MAX_GROWTH = 0.20
EXPLICIT_YEARS = 5
RATE_SHOCK = 0.01

FII_PREMIUM = 0.03
REAL_RATE_FLOOR = 0.03

CONFIRMATION_TOLERANCE = 0.30
WIDE_BAND_RATIO = 1.5

GRAHAM_PRODUCT = 22.5

RATE_BASE_AVERAGE = "selic_media_10a"
RATE_BASE_CURRENT = "selic_atual"
RATES_SOURCE_ESTIMATE = "estimativa"

PRINCIPAL_EARNINGS = "lucros_descontados"
PRINCIPAL_DIVIDENDS = "dividendos"

AGREEMENT_INSIDE = "dentro"
AGREEMENT_NEAR = "fora_ate_30"
AGREEMENT_FAR = "fora_mais_30"

METHOD_INPUT = {
    "dcf": "lucro",
    "bazin": "dividendo",
    "vpa": "patrimonio",
    "graham": "lucro_e_patrimonio",
}

_NO_METHOD_NOTE = {
    "etf": (
        "ETF de índice não tem método de preço justo: o preço dele acompanha o valor da carteira "
        "que carrega, e a distribuição é política do fundo"
    ),
    "bdr": (
        "a taxa de desconto disponível é em reais, e o lucro de uma empresa estrangeira não é: "
        "descontá-lo pela Selic faria todo BDR parecer caro"
    ),
}

_NO_METHOD_FALLBACK = "esta classe de ativo não tem método de preço justo"


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


def _hoje(reference: datetime | None) -> datetime:
    momento = reference or now_brt()
    return momento.astimezone(BRT) if momento.tzinfo else momento


def _media(valores: list[float]) -> float:
    return sum(valores) / len(valores)


def _mediana(valores: list[float]) -> float:
    ordenados = sorted(valores)
    meio = len(ordenados) // 2
    if len(ordenados) % 2:
        return ordenados[meio]
    return (ordenados[meio - 1] + ordenados[meio]) / 2


@dataclass(frozen=True)
class ValuationRates:
    discount_rate: float
    fii_yield: float
    rate_base: str
    selic_pct: float
    source: str | None = None
    as_of: float | None = None


def rates_for_valuation(rates: dict | None) -> ValuationRates | None:
    if not rates or rates.get("source") == RATES_SOURCE_ESTIMATE:
        return None

    media = rates.get("selic_media_10a")
    atual = rates.get("selic_anual")
    if media and media > 0:
        base, selic = RATE_BASE_AVERAGE, float(media)
    elif atual and atual > 0:
        base, selic = RATE_BASE_CURRENT, float(atual)
    else:
        return None

    juro_real = max(selic / 100 - INFLATION_TARGET, REAL_RATE_FLOOR)

    return ValuationRates(
        discount_rate=round(selic / 100 + EQUITY_RISK_PREMIUM, 4),
        fii_yield=round(juro_real + FII_PREMIUM, 4),
        rate_base=base,
        selic_pct=round(selic, 2),
        source=rates.get("source"),
        as_of=rates.get("fetched_at"),
    )


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

    today = _hoje(reference)
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


def _complete_years(dividends: list[dict[str, float]], years: int, today: datetime) -> list[float]:
    by_year = _dividends_by_year(dividends)
    oldest_allowed = today.year - years
    last_complete_year = today.year - 1
    covered = {y: v for y, v in by_year.items() if oldest_allowed <= y <= last_complete_year}
    if not covered:
        return []
    return [covered.get(y, 0.0) for y in range(min(covered), last_complete_year + 1)]


def average_dividend_last_n_years(
    dividends: list[dict[str, float]],
    years: int = DIVIDEND_WINDOW_YEARS,
    reference: datetime | None = None,
) -> float | None:
    if not dividends:
        return None

    today = _hoje(reference)
    values = _complete_years(dividends, years, today)
    if not values:
        return average_dividend_last_12m(dividends, reference=today)
    return _media(values)


def dividend_data_years(
    dividends: list[dict[str, float]],
    years: int = DIVIDEND_WINDOW_YEARS,
    reference: datetime | None = None,
) -> int:
    today = _hoje(reference)
    by_year = _dividends_by_year(dividends)
    return len([y for y in by_year if today.year - years <= y <= today.year - 1])


@dataclass(frozen=True)
class RecurringDividend:
    recurring: float | None
    mean: float | None
    last: float | None
    complete_years: int
    cut: bool
    capped: bool
    paid_years: int = 0


def recurring_dividend(
    dividends: list[dict[str, float]],
    reference: datetime | None = None,
) -> RecurringDividend:
    today = _hoje(reference)
    ttm = average_dividend_last_12m(dividends, reference=today) or 0.0
    values = _complete_years(dividends, DIVIDEND_WINDOW_YEARS, today)

    if not values:
        if ttm > 0:
            return RecurringDividend(ttm, ttm, ttm, 0, False, False)
        return RecurringDividend(None, None, None, 0, False, False)

    limitados = list(values)
    capped = False
    if len(values) >= MIN_DIVIDEND_YEARS:
        for i, valor in enumerate(values):
            teto = DIVIDEND_CAP_RATIO * _mediana(values[:i] + values[i + 1 :])
            if teto > 0 and valor > teto:
                limitados[i] = teto
                capped = True

    media = _media(limitados)
    ultimo = max(values[-1], ttm)
    recorrente = min(media, ultimo)

    return RecurringDividend(
        recurring=round(recorrente, 6) if recorrente > 0 else None,
        mean=round(media, 6) if media > 0 else None,
        last=round(ultimo, 6),
        complete_years=len(values),
        cut=media > 0 and ultimo < DIVIDEND_CUT_RATIO * media,
        capped=capped,
        paid_years=sum(1 for v in values if v > 0),
    )


@dataclass(frozen=True)
class NormalizedEarnings:
    eps: float | None
    years: int
    unstable: bool
    inconsistent: bool = False


def normalized_eps(
    eps: float | None,
    net_income_history: list[float | None] | None,
    net_income_ttm: float | None,
) -> NormalizedEarnings:
    if eps is None:
        return NormalizedEarnings(None, 0, False)

    anuais = [v for v in (net_income_history or []) if v is not None][:EARNINGS_YEARS]
    if len(anuais) < EARNINGS_YEARS:
        return NormalizedEarnings(eps, len(anuais), False)

    if eps == 0:
        return NormalizedEarnings(eps, len(anuais), True)
    base = net_income_ttm if net_income_ttm else anuais[0]
    if not base or (base > 0) != (eps > 0):
        return NormalizedEarnings(None, len(anuais), True, inconsistent=True)

    eps_n = eps * _media(anuais) / base
    instavel = (
        any(v <= 0 for v in anuais)
        or eps_n <= 0
        or not (1 / UNSTABLE_EARNINGS_RATIO <= eps / eps_n <= UNSTABLE_EARNINGS_RATIO)
    )
    return NormalizedEarnings(round(eps_n, 6), len(anuais), instavel)


def normalized_roe(
    roe_pct: float | None,
    net_income_history: list[float | None] | None,
    equity_history: list[float | None] | None,
) -> float | None:
    pares = [
        (lucro, patrimonio)
        for lucro, patrimonio in zip(net_income_history or [], equity_history or [], strict=False)
        if lucro is not None and patrimonio is not None
    ][:EARNINGS_YEARS]

    if len(pares) == EARNINGS_YEARS:
        patrimonio_medio = _media([p for _, p in pares])
        if patrimonio_medio <= 0:
            return None
        return round(_media([lucro for lucro, _ in pares]) / patrimonio_medio, 6)

    if roe_pct is None:
        return None
    return round(roe_pct / 100, 6)


def bazin_fair_price(
    avg_dividend: float | None, desired_yield: float = DEFAULT_DESIRED_YIELD
) -> float | None:
    if not avg_dividend or avg_dividend <= 0 or desired_yield <= 0:
        return None
    return round(avg_dividend / desired_yield, 2)


def graham_number(eps: float | None, book_value: float | None) -> float | None:
    if eps is None or book_value is None or eps <= 0 or book_value <= 0:
        return None
    return round(math.sqrt(GRAHAM_PRODUCT * eps * book_value), 2)


def earnings_value(
    eps: float,
    distributable: float,
    growth: float,
    discount_rate: float,
    roe: float,
    years: int = EXPLICIT_YEARS,
    long_run_growth: float = LONG_RUN_GROWTH,
) -> float:
    explicito = sum(
        eps * (1 + growth) ** t * distributable / (1 + discount_rate) ** t
        for t in range(1, years + 1)
    )
    distribuivel_longo = 1 - long_run_growth / roe
    terminal = (
        eps
        * (1 + growth) ** years
        * (1 + long_run_growth)
        * distribuivel_longo
        / ((discount_rate - long_run_growth) * (1 + discount_rate) ** years)
    )
    return explicito + terminal


def _breakeven_rate(
    price: float, eps: float, distributable: float, growth: float, roe: float
) -> float | None:
    baixo, alto = LONG_RUN_GROWTH + 0.005, 0.60
    valor_baixo = earnings_value(eps, distributable, growth, baixo, roe)
    valor_alto = earnings_value(eps, distributable, growth, alto, roe)
    if not (valor_alto <= price <= valor_baixo):
        return None
    for _ in range(60):
        meio = (baixo + alto) / 2
        if earnings_value(eps, distributable, growth, meio, roe) > price:
            baixo = meio
        else:
            alto = meio
    return round((baixo + alto) / 2, 4)


def _agreement(valor: float, piso: float, teto: float) -> str:
    if piso <= valor <= teto:
        return AGREEMENT_INSIDE
    distancia = (piso - valor) / piso if valor < piso else (valor - teto) / teto
    return AGREEMENT_NEAR if distancia <= CONFIRMATION_TOLERANCE else AGREEMENT_FAR


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


def margin_exact(
    price: float | None,
    fair_low: float | None,
    fair_high: float | None,
) -> float | None:
    if not price or price <= 0 or fair_low is None or fair_high is None:
        return None

    if price < fair_low:
        return round((fair_low - price) / fair_low, 9)

    if price > fair_high:
        return round((fair_high - price) / price, 9)

    return 0.0


def margin_of_safety_in_band(
    price: float | None,
    fair_low: float | None,
    fair_high: float | None,
) -> float | None:
    margem = margin_exact(price, fair_low, fair_high)
    return None if margem is None else round(margem, 4)


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

    principal: str | None = None

    quality_reasons: list[str] = field(default_factory=list)

    premises: dict = field(default_factory=dict)

    confirmation: dict | None = None

    indicators: list[dict] = field(default_factory=list)

    personal_ceiling: float | None = None

    details: dict = field(default_factory=dict)

    price: float | None = None

    principal_value: float | None = None

    dividend_recurring: float | None = None

    dividend_yield_recurring: float | None = None


@dataclass
class FairPriceInputs:
    asset_type: str
    price: float | None
    eps: float | None
    eps_normalized: float | None
    earnings_years: int
    earnings_unstable: bool
    roe: float | None
    book_value: float | None
    pvp: float | None
    dividend_recurring: float | None
    dividend_mean: float | None
    dividend_last: float | None
    dividend_complete_years: int
    dividend_cut: bool
    dividend_capped: bool
    dividend_12m: float | None
    data_years: int
    discount_rate: float | None = None
    fii_yield: float | None = None
    rate_base: str | None = None
    earnings_inconsistent: bool = False
    dividends_known: bool = True
    dividend_paid_years: int | None = None
    rate_source: str | None = None
    selic_pct: float | None = None
    rates_as_of: float | None = None
    reference_date: str | None = None

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def compute_fair_price_inputs(
    price: float | None,
    eps: float | None,
    book_value: float | None,
    dividends: list[dict[str, float]] | None,
    asset_type: str = "br_stock",
    pb_ratio: float | None = None,
    roe_pct: float | None = None,
    net_income_history: list[float | None] | None = None,
    equity_history: list[float | None] | None = None,
    net_income_ttm: float | None = None,
    rates: ValuationRates | None = None,
    reference: datetime | None = None,
) -> FairPriceInputs:
    today = _hoje(reference)
    proventos_conhecidos = dividends is not None
    dividends = dividends or []

    lucro = normalized_eps(eps, net_income_history, net_income_ttm)
    dividendo = recurring_dividend(dividends, reference=today)

    pvp: float | None = None
    if book_value and book_value > 0:
        if pb_ratio and pb_ratio > 0:
            pvp = round(pb_ratio, 2)
        elif price and price > 0:
            pvp = round(price / book_value, 2)

    return FairPriceInputs(
        asset_type=asset_type,
        price=price,
        eps=eps,
        eps_normalized=lucro.eps,
        earnings_years=lucro.years,
        earnings_unstable=lucro.unstable,
        roe=normalized_roe(roe_pct, net_income_history, equity_history),
        book_value=book_value,
        pvp=pvp,
        dividend_recurring=dividendo.recurring,
        dividend_mean=dividendo.mean,
        dividend_last=dividendo.last,
        dividend_complete_years=dividendo.complete_years,
        dividend_cut=dividendo.cut,
        dividend_capped=dividendo.capped,
        dividend_12m=average_dividend_last_12m(dividends, reference=today),
        data_years=dividend_data_years(dividends, reference=today),
        discount_rate=rates.discount_rate if rates else None,
        fii_yield=rates.fii_yield if rates else None,
        rate_base=rates.rate_base if rates else None,
        earnings_inconsistent=lucro.inconsistent,
        dividends_known=proventos_conhecidos,
        dividend_paid_years=dividendo.paid_years,
        rate_source=rates.source if rates else None,
        selic_pct=rates.selic_pct if rates else None,
        rates_as_of=rates.as_of if rates else None,
        reference_date=today.date().isoformat(),
    )


def _anos_pagos(inputs: FairPriceInputs) -> int:
    if inputs.dividend_paid_years is None:
        return inputs.dividend_complete_years
    return inputs.dividend_paid_years


def _rate_premises(inputs: FairPriceInputs) -> dict:
    return {
        "rate_base": inputs.rate_base,
        "rate_source": inputs.rate_source,
        "selic_pct": inputs.selic_pct,
        "rates_as_of": inputs.rates_as_of,
        "reference_date": inputs.reference_date,
    }


def _method(
    nome: str, papel: str, estado: str, nota: str = "", valor: float | None = None, **extra
) -> dict:
    return {
        "method": nome,
        "input": METHOD_INPUT[nome],
        "role": papel,
        "value": valor,
        "status": estado,
        "note": nota,
        **extra,
    }


@dataclass
class _Lens:
    central: float | None = None
    low: float | None = None
    high: float | None = None
    status: str = "ok"
    note: str = ""
    premises: dict = field(default_factory=dict)


def _earnings_lens(inputs: FairPriceInputs) -> _Lens:
    eps = inputs.eps_normalized
    d = inputs.discount_rate

    if eps is None and inputs.earnings_inconsistent:
        return _Lens(
            status="sem_dado",
            note=(
                "o LPA e o lucro informado para o período têm sinais opostos: um dos dois está "
                "errado"
            ),
        )
    if eps is None:
        return _Lens(status="sem_dado", note="lucro por ação não informado")
    if eps <= 0:
        return _Lens(status="lucro_negativo", note="a empresa não teve lucro no período")
    if d is None:
        return _Lens(
            status="sem_juro",
            note="sem juro de referência não há taxa para descontar o lucro",
        )
    if inputs.roe is None:
        return _Lens(
            status="sem_dado",
            note="sem ROE não há como saber quanto do lucro a empresa pode distribuir e crescer",
        )
    if inputs.roe <= LONG_RUN_GROWTH:
        return _Lens(
            status="roe_insuficiente",
            note=(
                "o retorno sobre o patrimônio não cobre o crescimento de longo prazo: crescer, "
                "aqui, consome valor em vez de criar"
            ),
        )
    if d - RATE_SHOCK <= LONG_RUN_GROWTH:
        return _Lens(status="taxa_implausivel", note="taxa de desconto abaixo do crescimento")
    if not inputs.dividends_known:
        return _Lens(
            status="sem_dado",
            note=(
                "o histórico de proventos não chegou da fonte: sem ele não há como separar o que "
                "a empresa distribui do que retém para crescer"
            ),
        )

    payout = min(max((inputs.dividend_recurring or 0.0) / eps, 0.0), 1.0)
    crescimento = min(max(inputs.roe * (1 - payout), 0.0), MAX_GROWTH)
    distribuivel = 1 - crescimento / inputs.roe

    def com(taxa: float) -> float:
        return earnings_value(eps, distribuivel, crescimento, taxa, inputs.roe)

    def sem(taxa: float) -> float:
        return earnings_value(eps, 1.0, 0.0, taxa, inputs.roe)

    central = com(d)
    sem_crescimento = sem(d)
    piso = min(com(d + RATE_SHOCK), sem(d + RATE_SHOCK))
    teto = max(com(d - RATE_SHOCK), sem(d - RATE_SHOCK))

    return _Lens(
        central=round(central, 2),
        low=round(piso, 2),
        high=round(teto, 2),
        premises={
            "discount_rate": d,
            **_rate_premises(inputs),
            "growth": round(crescimento, 4),
            "long_run_growth": LONG_RUN_GROWTH,
            "explicit_years": EXPLICIT_YEARS,
            "roe": round(inputs.roe, 4),
            "payout": round(payout, 4),
            "distributable": round(distribuivel, 4),
            "eps_normalized": round(eps, 4),
            "earnings_years": inputs.earnings_years,
            "value_without_growth": round(sem_crescimento, 2),
            "growth_creates_value": central > sem_crescimento,
            "breakeven_discount_rate": (
                _breakeven_rate(inputs.price, eps, distribuivel, crescimento, inputs.roe)
                if inputs.price and inputs.price > 0
                else None
            ),
        },
    )


def _dividend_lens(inputs: FairPriceInputs) -> _Lens:
    y = inputs.fii_yield
    d = inputs.dividend_recurring

    if not inputs.dividends_known:
        return _Lens(status="sem_dado", note="o histórico de distribuições não chegou da fonte")
    if not d:
        return _Lens(status="sem_dado", note="sem distribuição recorrente no período")
    if y is None:
        return _Lens(
            status="sem_juro",
            note="sem juro de referência não há yield exigido para capitalizar a distribuição",
        )

    return _Lens(
        central=round(d / y, 2),
        low=round(d / (y + RATE_SHOCK), 2),
        high=round(d / (y - RATE_SHOCK), 2),
        premises={
            "fii_yield": y,
            **_rate_premises(inputs),
            "inflation_target": INFLATION_TARGET,
            "real_rate_floor": REAL_RATE_FLOOR,
            "fii_premium": FII_PREMIUM,
            "dividend_recurring": round(d, 4),
        },
    )


def _stock_confirmation(inputs: FairPriceInputs, lens: _Lens) -> dict:
    d = inputs.dividend_recurring
    taxa = inputs.discount_rate

    if not d or _anos_pagos(inputs) < MIN_DIVIDEND_YEARS:
        return _method(
            "bazin",
            "confirmacao",
            "sem_dado",
            f"menos de {MIN_DIVIDEND_YEARS} anos com dividendo: não há série para confirmar o lucro",
        )
    if lens.premises.get("payout", 0.0) < LOW_PAYOUT:
        return _method(
            "bazin",
            "confirmacao",
            "pouco_distribuido",
            "a empresa distribui pouco do lucro: o dividendo não mede a capacidade dela",
        )

    crescimento = min(lens.premises["growth"], LONG_RUN_GROWTH)
    valor = round(d * (1 + crescimento) / (taxa - crescimento), 2)
    return _method(
        "bazin",
        "confirmacao",
        "ok",
        valor=valor,
        agreement=_agreement(valor, lens.low, lens.high),
    )


def _fii_confirmation(inputs: FairPriceInputs, lens: _Lens) -> dict:
    vpa = inputs.book_value
    if not vpa or vpa <= 0:
        return _method("vpa", "confirmacao", "sem_dado", "sem valor patrimonial informado")
    return _method(
        "vpa",
        "confirmacao",
        "ok",
        valor=round(vpa, 2),
        agreement=_agreement(vpa, lens.low, lens.high),
    )


def _quality(
    inputs: FairPriceInputs, lens: _Lens, confirmacao: dict, principal: str
) -> tuple[str, list[str]]:
    frageis: list[str] = []
    amplas: list[str] = []

    if principal == PRINCIPAL_EARNINGS:
        if inputs.earnings_years < EARNINGS_YEARS:
            frageis.append(
                f"o lucro vem de {inputs.earnings_years or 'nenhum'} exercício(s) anual(is), e "
                f"normalizá-lo exige {EARNINGS_YEARS}"
            )
        if inputs.earnings_unstable:
            frageis.append(
                "o lucro oscila demais entre os exercícios: o dos últimos 12 meses se afasta da "
                "média, ou algum ano teve prejuízo"
            )
    elif _anos_pagos(inputs) < MIN_DIVIDEND_YEARS:
        frageis.append(
            f"a distribuição tem {_anos_pagos(inputs)} ano(s) completo(s) com pagamento, e o "
            f"recorrente exige {MIN_DIVIDEND_YEARS}"
        )

    if inputs.dividend_cut:
        frageis.append(
            "a distribuição mais recente caiu para menos da metade da média: o recorrente usa a "
            "mais recente"
        )

    concordancia = confirmacao.get("agreement")
    if confirmacao["status"] != "ok":
        amplas.append(f"sem confirmação independente — {confirmacao['note']}")
    elif concordancia == AGREEMENT_FAR and principal == PRINCIPAL_EARNINGS:
        amplas.append(
            f"a leitura pelos dividendos fica a mais de {CONFIRMATION_TOLERANCE:.0%} da faixa: ela "
            "usa a mesma taxa e o crescimento do principal, e se afasta dele quando o payout se "
            "afasta do que o modelo distribui no longo prazo"
        )
    elif concordancia == AGREEMENT_FAR:
        frageis.append(
            f"a leitura de confirmação discorda da faixa em mais de {CONFIRMATION_TOLERANCE:.0%}"
        )
    elif concordancia == AGREEMENT_NEAR:
        amplas.append(
            f"a leitura de confirmação fica fora da faixa, a até {CONFIRMATION_TOLERANCE:.0%} dela"
        )

    largura = lens.high / lens.low if lens.low and lens.high else None
    if principal == PRINCIPAL_EARNINGS and largura and largura > WIDE_BAND_RATIO:
        amplas.append(
            f"a faixa é larga: o teto passa de {WIDE_BAND_RATIO:.1f}× o piso, porque a premissa "
            "de crescimento pesa muito"
        )

    if frageis:
        return "fragil", frageis
    if amplas:
        return "ampla", amplas
    return "firme", ["a faixa é estreita e a leitura de confirmação cai dentro dela"]


def _indicators(inputs: FairPriceInputs, desired_yield: float) -> tuple[list[dict], float | None]:
    price = inputs.price
    itens: list[dict] = []

    graham = graham_number(inputs.eps_normalized, inputs.book_value)
    if graham is not None:
        itens.append(
            {
                "kind": "graham",
                "value": graham,
                "passes": bool(price and price <= graham),
                "note": (
                    "critério do investidor defensivo de Graham: P/L vezes P/VP até 22,5. É "
                    "triagem, não preço justo"
                ),
            }
        )

    teto_pessoal = bazin_fair_price(inputs.dividend_recurring, desired_yield)
    if teto_pessoal is not None:
        itens.append(
            {
                "kind": "preco_teto_pessoal",
                "value": teto_pessoal,
                "passes": bool(price and price <= teto_pessoal),
                "desired_yield": desired_yield,
                "note": f"o preço até o qual a distribuição recorrente rende {desired_yield:.0%}",
            }
        )

    if inputs.pvp is not None:
        itens.append({"kind": "pvp", "value": inputs.pvp, "passes": None, "note": ""})

    return itens, teto_pessoal


def _no_band_methods(inputs: FairPriceInputs, lens: _Lens | None, principal: str | None) -> list:
    if principal is None:
        nota = _NO_METHOD_NOTE.get(inputs.asset_type, _NO_METHOD_FALLBACK)
        return [
            _method(nome, "inaplicavel", "inaplicavel", nota) for nome in ("dcf", "bazin", "vpa")
        ]

    metodos = []
    if principal == PRINCIPAL_EARNINGS:
        metodos.append(
            _method("dcf", "principal", lens.status, lens.note)
            if lens
            else _method("dcf", "principal", "sem_dado")
        )
        metodos.append(_method("vpa", "inaplicavel", "inaplicavel", "vale para FII"))
    else:
        metodos.append(
            _method("bazin", "principal", lens.status, lens.note)
            if lens
            else _method("bazin", "principal", "sem_dado")
        )
        metodos.append(_method("dcf", "inaplicavel", "inaplicavel", "vale para ação"))
    return metodos


def fair_price_from_inputs(
    inputs: FairPriceInputs,
    desired_yield: float | None = None,
) -> FairPriceResult:
    asset_type = inputs.asset_type
    price = inputs.price

    effective_yield = (
        desired_yield if desired_yield and desired_yield > 0 else desired_yield_for(asset_type)
    )
    indicadores, teto_pessoal = _indicators(inputs, effective_yield)
    graham = next((i["value"] for i in indicadores if i["kind"] == "graham"), None)

    dy_12m = (
        round(inputs.dividend_12m / price, 4)
        if (inputs.dividend_12m is not None and price and price > 0)
        else None
    )
    dy_5y = (
        round(inputs.dividend_recurring / price, 4)
        if (inputs.dividend_recurring is not None and price and price > 0)
        else None
    )

    base = {
        "price": price,
        "graham": graham,
        "avg_dividend_5y": (
            round(inputs.dividend_recurring, 4) if inputs.dividend_recurring else None
        ),
        "dy_12m": dy_12m,
        "dy_5y": dy_5y,
        "data_years": inputs.data_years,
        "desired_yield_used": effective_yield,
        "dividend_recurring": (
            round(inputs.dividend_recurring, 4) if inputs.dividend_recurring else None
        ),
        "dividend_yield_recurring": dy_5y,
        "pvp": inputs.pvp,
        "indicators": indicadores,
        "personal_ceiling": teto_pessoal,
    }

    lens: _Lens | None = None
    principal: str | None = None
    if asset_type == "fii":
        principal = PRINCIPAL_DIVIDENDS
        lens = _dividend_lens(inputs)
    elif asset_type == "br_stock":
        principal = PRINCIPAL_EARNINGS
        lens = _earnings_lens(inputs)

    if lens is None or lens.central is None:
        return FairPriceResult(
            bazin=None,
            dcf=None,
            consensus=None,
            consensus_methods=0,
            margin_of_safety=None,
            principal=principal,
            methods=_no_band_methods(inputs, lens, principal),
            **base,
        )

    if principal == PRINCIPAL_EARNINGS:
        confirmacao = _stock_confirmation(inputs, lens)
        metodos = [
            _method("dcf", "principal", "ok", valor=lens.central),
            confirmacao,
            _method("vpa", "inaplicavel", "inaplicavel", "vale para FII"),
        ]
        bazin = confirmacao["value"]
        dcf = lens.central
    else:
        confirmacao = _fii_confirmation(inputs, lens)
        metodos = [
            _method("bazin", "principal", "ok", valor=lens.central),
            confirmacao,
            _method("dcf", "inaplicavel", "inaplicavel", "vale para ação"),
        ]
        bazin = lens.central
        dcf = None

    if graham is not None:
        metodos.append(_method("graham", "indicador", "ok", valor=graham))

    qualidade, razoes = _quality(inputs, lens, confirmacao, principal)

    confirmado = confirmacao["status"] == "ok"
    dispersao = (
        round(max(lens.central, confirmacao["value"]) / min(lens.central, confirmacao["value"]), 2)
        if confirmado and confirmacao["value"] > 0
        else None
    )

    return FairPriceResult(
        bazin=bazin,
        dcf=dcf,
        consensus=lens.central,
        principal_value=lens.central,
        consensus_methods=2 if confirmado else 1,
        margin_of_safety=margin_of_safety_in_band(price, lens.low, lens.high),
        fair_low=lens.low,
        fair_high=lens.high,
        band_position=band_position(price, lens.low, lens.high),
        band_quality=qualidade,
        independent_inputs=2 if confirmado else 1,
        methods=metodos,
        method_dispersion=dispersao,
        methods_disagree=confirmacao.get("agreement") == AGREEMENT_FAR,
        principal=principal,
        quality_reasons=razoes,
        premises={
            **lens.premises,
            "dividend_cut": inputs.dividend_cut,
            "dividend_capped": inputs.dividend_capped,
        },
        confirmation=(
            {
                "method": confirmacao["method"],
                "value": confirmacao["value"],
                "agreement": confirmacao.get("agreement"),
            }
            if confirmado
            else None
        ),
        **base,
    )


def compute_fair_price(
    price: float | None,
    eps: float | None,
    book_value: float | None,
    dividends: list[dict[str, float]] | None,
    asset_type: str = "br_stock",
    desired_yield: float | None = None,
    pb_ratio: float | None = None,
    roe_pct: float | None = None,
    net_income_history: list[float | None] | None = None,
    equity_history: list[float | None] | None = None,
    net_income_ttm: float | None = None,
    rates: ValuationRates | None = None,
    reference: datetime | None = None,
) -> FairPriceResult:
    inputs = compute_fair_price_inputs(
        price=price,
        eps=eps,
        book_value=book_value,
        dividends=dividends,
        asset_type=asset_type,
        pb_ratio=pb_ratio,
        roe_pct=roe_pct,
        net_income_history=net_income_history,
        equity_history=equity_history,
        net_income_ttm=net_income_ttm,
        rates=rates,
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

    variacoes = [values[i] - values[i - 1] for i in range(1, len(values))]
    ganho = sum(max(v, 0.0) for v in variacoes[:period]) / period
    perda = sum(max(-v, 0.0) for v in variacoes[:period]) / period

    for v in variacoes[period:]:
        ganho = (ganho * (period - 1) + max(v, 0.0)) / period
        perda = (perda * (period - 1) + max(-v, 0.0)) / period

    if perda == 0:
        return 100.0

    return round(100 - (100 / (1 + ganho / perda)), 2)


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
