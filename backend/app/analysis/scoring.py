from __future__ import annotations

from app.models.enums import RiskProfile


def _clip(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _score_quality(roe: float | None, margin: float | None) -> float | None:
    parts = []
    if roe is not None:
        parts.append(_clip(roe * 4))
    if margin is not None:
        parts.append(_clip(margin * 5))
    if not parts:
        return None
    return sum(parts) / len(parts)


def _score_dividend(dy: float | None) -> float | None:
    if dy is None:
        return None
    return _clip(dy * 12.5)


def _score_leverage(de: float | None) -> float | None:
    if de is None:
        return None
    return _clip(100 - de / 2)


def _score_growth(rev_growth: float | None) -> float | None:
    if rev_growth is None:
        return None
    return _clip((rev_growth + 10) * (100 / 30))


def _score_mos(margin_of_safety: float | None) -> float | None:
    if margin_of_safety is None:
        return None
    return _clip(50 + margin_of_safety * 100)


OPPORTUNITY_WEIGHTS: dict[RiskProfile, dict[str, float]] = {
    RiskProfile.conservative: {
        "mos": 0.30,
        "quality": 0.20,
        "dividend": 0.25,
        "leverage": 0.15,
        "growth": 0.05,
    },
    RiskProfile.moderate: {
        "mos": 0.30,
        "quality": 0.20,
        "dividend": 0.15,
        "leverage": 0.10,
        "growth": 0.15,
    },
    RiskProfile.aggressive: {
        "mos": 0.20,
        "quality": 0.20,
        "dividend": 0.05,
        "leverage": 0.05,
        "growth": 0.40,
    },
}

FII_WEIGHTS: dict[RiskProfile, dict[str, float]] = {
    RiskProfile.conservative: {"mos": 0.40, "dividend": 0.60},
    RiskProfile.moderate: {"mos": 0.50, "dividend": 0.50},
    RiskProfile.aggressive: {"mos": 0.65, "dividend": 0.35},
}


def score_opportunity(
    asset_type: str,
    margin_of_safety: float | None,
    dividend_yield: float | None,
    roe: float | None,
    profit_margin: float | None,
    debt_to_equity: float | None,
    revenue_growth: float | None,
    profile: RiskProfile = RiskProfile.moderate,
) -> tuple[float, dict[str, float]]:
    if asset_type == "etf":
        return 0.0, {"data_completeness": 0.0}

    if asset_type == "fii":
        dimensions: dict[str, float | None] = {
            "mos": _score_mos(margin_of_safety),
            "dividend": _score_dividend(dividend_yield),
        }
        weights = FII_WEIGHTS[profile]
    else:
        dimensions = {
            "mos": _score_mos(margin_of_safety),
            "quality": _score_quality(roe, profit_margin),
            "dividend": _score_dividend(dividend_yield),
            "leverage": _score_leverage(debt_to_equity),
            "growth": _score_growth(revenue_growth),
        }
        weights = OPPORTUNITY_WEIGHTS[profile]

    available = {k: v for k, v in dimensions.items() if v is not None}
    available_weight = sum(weights[k] for k in available)
    total_weight = sum(weights.values())

    data_completeness = round(available_weight / total_weight, 4) if total_weight else 0.0

    if not available or available_weight <= 0:
        return 0.0, {"data_completeness": 0.0}

    total = sum(weights[k] * available[k] for k in available) / available_weight

    breakdown = {k: round(v, 2) for k, v in available.items()}
    breakdown["data_completeness"] = data_completeness

    return round(total, 2), breakdown
