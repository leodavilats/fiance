from __future__ import annotations

import math

from app.models.enums import RiskProfile

# Este arquivo tinha ~200 linhas mortas: `score_company`, `rank`,
# `PROFILE_WEIGHTS`, `_score_value`, `_score_pvp`, `_compute_sector_medians`,
# `_score_fii`, `_score_etf` e `_rationale` — um modelo alternativo baseado em
# P/L·P/VP, sem nenhum consumidor, convivendo com o modelo real baseado em
# margem de segurança. Foram removidos: o risco não era desperdício de linhas,
# era um dev futuro corrigir o arquivo errado.


def _clip(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


# --- dimensões ------------------------------------------------------------
#
# Cada dimensão devolve `None` quando o insumo não existe. Antes a ausência era
# codificada como número: _score_dividend(None) -> 0.0 (indistinguível de
# "péssimo") enquanto _score_leverage(None) -> 50.0 e _score_growth(None) ->
# 30.0 (chutes silenciosos). Com peso 0.40 em dividendos, um FII sem dado na
# BRAPI era indistinguível de um FII ruim.


def _score_quality(roe: float | None, margin: float | None) -> float | None:
    """ROE e margem em **percentual** (20.0 = 20%)."""
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
    """D/E em percentual (60.0 = dívida de 60% do patrimônio)."""
    if de is None:
        return None
    return _clip(100 - de / 2)


def _score_growth(rev_growth: float | None) -> float | None:
    if rev_growth is None:
        return None
    return _clip((rev_growth + 10) * (100 / 30))


def _score_liquidity(market_cap: float | None) -> float | None:
    if not market_cap or market_cap <= 0:
        return None
    return _clip((math.log10(market_cap) - 7) * 30)


def _score_technical(rsi_14: float | None, trend: str) -> float | None:
    if rsi_14 is None and trend in ("unknown", ""):
        return None

    rsi = rsi_14 if rsi_14 is not None else 50.0
    score = 50.0 + (60.0 - rsi) * 0.5

    if trend == "uptrend":
        score += 10
    elif trend == "downtrend":
        score -= 10

    return _clip(score)


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
        "technical": 0.05,
    },
    RiskProfile.moderate: {
        "mos": 0.30,
        "quality": 0.20,
        "dividend": 0.15,
        "leverage": 0.10,
        "growth": 0.15,
        "technical": 0.10,
    },
    RiskProfile.aggressive: {
        "mos": 0.20,
        "quality": 0.20,
        "dividend": 0.05,
        "leverage": 0.05,
        "growth": 0.40,
        "technical": 0.10,
    },
}

_FII_WEIGHTS = {"mos": 0.45, "dividend": 0.40, "liquidity": 0.15}
_ETF_WEIGHTS = {"mos": 0.55, "dividend": 0.30, "liquidity": 0.15}

# Abaixo disso o score é chute, não medida: a UI deve apresentá-lo como
# "sem dado suficiente" em vez de colorir uma nota.
MIN_DATA_COMPLETENESS = 0.5


def score_opportunity(
    asset_type: str,
    margin_of_safety: float | None,
    dividend_yield: float | None,
    roe: float | None,
    profit_margin: float | None,
    debt_to_equity: float | None,
    revenue_growth: float | None,
    market_cap: float | None,
    rsi_14: float | None,
    trend: str,
    profile: RiskProfile = RiskProfile.moderate,
) -> tuple[float, dict[str, float]]:
    """Score composto 0-100 de oportunidade.

    Margem de segurança (preço justo) + fundamentos (qualidade, endividamento,
    crescimento) + dividendos + técnico, ponderados pelo perfil de risco.
    FII/ETF usam um subconjunto (sem LPA/ROE/dívida de empresa aplicável).

    Os pesos são **renormalizados sobre as dimensões disponíveis**: um ativo sem
    dado de dividendo é pontuado pelo que se sabe dele, e o breakdown carrega
    `data_completeness` para a UI poder dizer "não sei" em vez de "ruim".
    """
    if asset_type in ("fii", "etf"):
        dimensions: dict[str, float | None] = {
            "mos": _score_mos(margin_of_safety),
            "dividend": _score_dividend(dividend_yield),
            "liquidity": _score_liquidity(market_cap),
        }
        weights = _FII_WEIGHTS if asset_type == "fii" else _ETF_WEIGHTS
    else:
        dimensions = {
            "mos": _score_mos(margin_of_safety),
            "quality": _score_quality(roe, profit_margin),
            "dividend": _score_dividend(dividend_yield),
            "leverage": _score_leverage(debt_to_equity),
            "growth": _score_growth(revenue_growth),
            "technical": _score_technical(rsi_14, trend),
        }
        weights = OPPORTUNITY_WEIGHTS[profile]

    available = {k: v for k, v in dimensions.items() if v is not None}
    available_weight = sum(weights[k] for k in available)
    total_weight = sum(weights.values())

    data_completeness = round(available_weight / total_weight, 4) if total_weight else 0.0

    if not available or available_weight <= 0:
        return 0.0, {"data_completeness": 0.0}

    # Renormaliza: sem isso, cada dimensão faltante puxava o score para baixo
    # com peso cheio e valor arbitrário.
    total = sum(weights[k] * available[k] for k in available) / available_weight

    breakdown = {k: round(v, 2) for k, v in available.items()}
    breakdown["data_completeness"] = data_completeness

    return round(total, 2), breakdown
