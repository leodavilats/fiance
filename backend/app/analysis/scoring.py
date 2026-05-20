from __future__ import annotations

from typing import Dict, List, Optional

from app.models.company import CompanyFundamentals, ScoredCompany
from app.models.enums import RiskProfile

PROFILE_WEIGHTS: Dict[RiskProfile, Dict[str, float]] = {

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

def _score_value(pe: Optional[float], pb: Optional[float]) -> float:

    score = 50.0

    if pe is not None and pe > 0:

        score_pe = _clip(100 - (pe - 5) * 5)

    else:

        score_pe = 30.0

    if pb is not None and pb > 0:

        score_pb = _clip(100 - (pb - 0.5) * 28.5)

    else:

        score_pb = 30.0

    return (score_pe + score_pb) / 2

def _score_quality(roe: Optional[float], margin: Optional[float]) -> float:

    score_roe = _clip((roe or 0) * 4)

    score_margin = _clip((margin or 0) * 5)

    return (score_roe + score_margin) / 2

def _score_dividend(dy: Optional[float]) -> float:

    if dy is None:

        return 0.0

    return _clip(dy * 12.5)

def _score_leverage(de: Optional[float]) -> float:

    if de is None:

        return 50.0

    return _clip(100 - de / 2)

def _score_growth(rev_growth: Optional[float]) -> float:

    if rev_growth is None:

        return 30.0

    return _clip((rev_growth + 10) * (100 / 30))

def _rationale(f: CompanyFundamentals, breakdown: Dict[str, float]) -> str:

    tags: List[str] = []

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

def score_company(f: CompanyFundamentals, profile: RiskProfile) -> ScoredCompany:

    weights = PROFILE_WEIGHTS[profile]

    breakdown = {

        "value": _score_value(f.pe_ratio, f.pb_ratio),

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

def rank(

    companies: List[CompanyFundamentals],

    profile: RiskProfile,

    exclude_sectors: Optional[List[str]] = None,

) -> List[ScoredCompany]:

    excluded = {s.lower() for s in (exclude_sectors or [])}

    scored = [

        score_company(c, profile)

        for c in companies

        if c.price and c.price > 0 and (c.sector or "").lower() not in excluded

    ]

    scored.sort(key=lambda s: s.score, reverse=True)

    return scored

