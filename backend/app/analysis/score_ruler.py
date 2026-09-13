from __future__ import annotations

SCORE_STRONG = 75.0
SCORE_GOOD = 60.0
SCORE_NEUTRAL = 40.0

HIGHLIGHT_MIN_DY = 6.0

MIN_DATA_COMPLETENESS = 0.5

_BANDS = (
    (SCORE_STRONG, "Excelente entrada"),
    (SCORE_GOOD, "Boa oportunidade"),
    (SCORE_NEUTRAL, "Neutro"),
)


def score_band(score: float) -> str:
    for threshold, label in _BANDS:
        if score >= threshold:
            return label
    return "Evitar agora"


def score_confiavel(data_completeness: float | None) -> bool:
    return (1.0 if data_completeness is None else data_completeness) >= MIN_DATA_COMPLETENESS


def is_highlight(verdict: str, score: float, dividend_yield: float | None) -> bool:
    if verdict == "STRONG_BUY":
        return True
    return score >= SCORE_STRONG and (dividend_yield or 0.0) >= HIGHLIGHT_MIN_DY
