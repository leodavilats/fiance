from __future__ import annotations

import math
import statistics

from app.collectors.universal import detect_type
from app.models.company import CompanyFundamentals, ScoredCompany
from app.models.enums import RiskProfile

PROFILE_WEIGHTS: dict[RiskProfile, dict[str, float]] = {
    RiskProfile.conservative: {
        "value": 0.20,
        "quality": 0.30,
        "dividend": 0.30,
        "leverage": 0.15,
        "growth": 0.05,
    },
    RiskProfile.moderate: {
        "value": 0.20,
        "quality": 0.30,
        "dividend": 0.15,
        "leverage": 0.15,
        "growth": 0.20,
    },
    RiskProfile.aggressive: {
        "value": 0.10,
        "quality": 0.25,
        "dividend": 0.05,
        "leverage": 0.10,
        "growth": 0.50,
    },
}


def _clip(v: float, lo: float = 0.0, hi: float = 100.0) -> float:

    return max(lo, min(hi, v))


def _score_relative(value: float, sector_median: float) -> float:
    ratio = value / sector_median
    return _clip(150 - ratio * 100)


def _score_value(
    pe: float | None,
    pb: float | None,
    sector_pe_median: float | None = None,
    sector_pb_median: float | None = None,
) -> float:

    if pe is not None and pe > 0:
        score_pe = _clip(100 - (pe - 5) * 5)
        if sector_pe_median and sector_pe_median > 0:
            score_pe = (score_pe + _score_relative(pe, sector_pe_median)) / 2

    else:
        score_pe = 30.0

    if pb is not None and pb > 0:
        score_pb = _clip(100 - (pb - 0.5) * 28.5)
        if sector_pb_median and sector_pb_median > 0:
            score_pb = (score_pb + _score_relative(pb, sector_pb_median)) / 2

    else:
        score_pb = 30.0

    return (score_pe + score_pb) / 2


def _score_quality(roe: float | None, margin: float | None) -> float:

    score_roe = _clip((roe or 0) * 4)

    score_margin = _clip((margin or 0) * 5)

    return (score_roe + score_margin) / 2


def _score_dividend(dy: float | None) -> float:

    if dy is None:
        return 0.0

    return _clip(dy * 12.5)


def _score_leverage(de: float | None) -> float:

    if de is None:
        return 50.0

    return _clip(100 - de / 2)


def _score_growth(rev_growth: float | None) -> float:

    if rev_growth is None:
        return 30.0

    return _clip((rev_growth + 10) * (100 / 30))


def _score_pvp(pvp: float | None) -> float:
    if pvp is None or pvp <= 0:
        return 50.0

    return _clip(100 - (pvp - 0.7) * 100)


def _score_liquidity(market_cap: float | None) -> float:
    if not market_cap or market_cap <= 0:
        return 50.0

    return _clip((math.log10(market_cap) - 7) * 30)


def _score_fii(f: CompanyFundamentals) -> ScoredCompany:
    breakdown = {
        "dividend": _score_dividend(f.dividend_yield),
        "value": _score_pvp(f.pb_ratio),
        "liquidity": _score_liquidity(f.market_cap),
    }
    weights = {"dividend": 0.50, "value": 0.35, "liquidity": 0.15}

    total = sum(weights[k] * breakdown[k] for k in weights)

    tags: list[str] = []
    if f.dividend_yield:
        tags.append(f"DY {f.dividend_yield:.1f}% a.a.")
    if f.pb_ratio:
        tags.append(f"P/VP {f.pb_ratio:.2f}" + (" (desconto)" if f.pb_ratio < 1 else ""))
    if not tags:
        tags.append("Fundo imobiliário")

    return ScoredCompany(
        fundamentals=f,
        score=round(total, 2),
        breakdown={k: round(v, 2) for k, v in breakdown.items()},
        rationale=" · ".join(tags[:3]),
    )


def _score_etf(f: CompanyFundamentals) -> ScoredCompany:
    # ETF é uma cota de fundo, não uma empresa — sem EPS/ROE/margem, então o
    # score usa dividend yield (quando o ETF distribui) e liquidez como proxy de qualidade.
    breakdown = {
        "dividend": _score_dividend(f.dividend_yield),
        "liquidity": _score_liquidity(f.market_cap),
    }
    weights = {"dividend": 0.5, "liquidity": 0.5}

    total = sum(weights[k] * breakdown[k] for k in weights)

    tags: list[str] = []
    if f.dividend_yield:
        tags.append(f"DY {f.dividend_yield:.1f}% a.a.")
    tags.append(
        "ETF — avaliação por dividend yield e liquidez, fora do modelo fundamentalista de empresa."
    )

    return ScoredCompany(
        fundamentals=f,
        score=round(total, 2),
        breakdown={k: round(v, 2) for k, v in breakdown.items()},
        rationale=" · ".join(tags[:3]),
    )


def _rationale(f: CompanyFundamentals, breakdown: dict[str, float]) -> str:

    tags: list[str] = []

    if breakdown.get("dividend", 0) >= 70 and f.dividend_yield:
        tags.append(f"Boa pagadora de dividendos ({f.dividend_yield:.1f}% a.a.)")

    elif f.dividend_yield and f.dividend_yield >= 4:
        tags.append(f"Paga dividendos ({f.dividend_yield:.1f}% a.a.)")

    if breakdown.get("quality", 0) >= 70:
        tags.append("Empresa muito lucrativa")

    elif breakdown.get("quality", 0) >= 50:
        tags.append("Boa lucratividade")

    if breakdown.get("value", 0) >= 70:
        tags.append("Preço atrativo frente aos lucros")

    if breakdown.get("growth", 0) >= 70:
        tags.append("Em forte crescimento")

    elif breakdown.get("growth", 0) <= 25:
        tags.append("Crescimento fraco")

    if breakdown.get("leverage", 0) >= 70:
        tags.append("Pouco endividada")

    elif breakdown.get("leverage", 0) <= 25:
        tags.append("Bastante endividada")

    if not tags:
        tags.append("Perfil equilibrado")

    return " · ".join(tags[:3])


def score_company(
    f: CompanyFundamentals,
    profile: RiskProfile,
    asset_type: str | None = None,
    sector_medians: dict[str, tuple[float, float]] | None = None,
) -> ScoredCompany:

    at = asset_type or detect_type(f.ticker)

    if at == "fii":
        return _score_fii(f)

    if at == "etf":
        return _score_etf(f)

    weights = PROFILE_WEIGHTS[profile]

    sector_pe_median, sector_pb_median = (sector_medians or {}).get(
        (f.sector or "").lower(), (None, None)
    )

    breakdown = {
        "value": _score_value(f.pe_ratio, f.pb_ratio, sector_pe_median, sector_pb_median),
        "quality": _score_quality(f.roe, f.profit_margin),
        "dividend": _score_dividend(f.dividend_yield),
        "leverage": _score_leverage(f.debt_to_equity),
        "growth": _score_growth(f.revenue_growth),
    }

    total = sum(weights[k] * breakdown[k] for k in weights)

    return ScoredCompany(
        fundamentals=f,
        score=round(total, 2),
        breakdown={k: round(v, 2) for k, v in breakdown.items()},
        rationale=_rationale(f, breakdown),
    )


def _compute_sector_medians(
    companies: list[CompanyFundamentals],
) -> dict[str, tuple[float, float]]:
    pe_by_sector: dict[str, list[float]] = {}
    pb_by_sector: dict[str, list[float]] = {}

    for c in companies:
        sector = (c.sector or "").lower()
        if not sector:
            continue
        if c.pe_ratio and c.pe_ratio > 0:
            pe_by_sector.setdefault(sector, []).append(c.pe_ratio)
        if c.pb_ratio and c.pb_ratio > 0:
            pb_by_sector.setdefault(sector, []).append(c.pb_ratio)

    sectors = set(pe_by_sector) | set(pb_by_sector)
    medians = {}
    for sector in sectors:
        pe_values = pe_by_sector.get(sector, [])
        pb_values = pb_by_sector.get(sector, [])
        pe_median = statistics.median(pe_values) if len(pe_values) >= 3 else None
        pb_median = statistics.median(pb_values) if len(pb_values) >= 3 else None
        medians[sector] = (pe_median, pb_median)

    return medians


def rank(
    companies: list[CompanyFundamentals],
    profile: RiskProfile,
    exclude_sectors: list[str] | None = None,
) -> list[ScoredCompany]:

    excluded = {s.lower() for s in (exclude_sectors or [])}

    eligible = [
        c for c in companies if c.price and c.price > 0 and (c.sector or "").lower() not in excluded
    ]

    sector_medians = _compute_sector_medians(eligible)

    scored = [score_company(c, profile, sector_medians=sector_medians) for c in eligible]

    scored.sort(key=lambda s: s.score, reverse=True)

    return scored
