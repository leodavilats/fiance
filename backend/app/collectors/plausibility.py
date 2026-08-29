from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("fiance.plausibility")


@dataclass(frozen=True)
class Range:
    low: float
    high: float
    reason: str
    critical: bool = False

    def accepts(self, value: float) -> bool:
        return self.low <= value <= self.high


RANGES: dict[str, Range] = {
    "price": Range(
        0.01,
        1_000_000.0,
        "Ação abaixo de um centavo não negocia; acima de um milhão não existe na B3.",
        critical=True,
    ),
    "market_cap": Range(
        1_000.0,
        1e14,
        "Valor de mercado menor que mil reais é campo zerado, não empresa.",
    ),
    "pe_ratio": Range(
        -1_000.0,
        1_000.0,
        "P/L fora disso é lucro perto de zero, e a razão perde significado.",
    ),
    "pb_ratio": Range(
        -100.0,
        1_000.0,
        "P/VP fora disso é patrimônio perto de zero.",
    ),
    "eps": Range(-100_000.0, 100_000.0, "Lucro por ação em ordem de grandeza plausível."),
    "book_value": Range(-100_000.0, 1_000_000.0, "Valor patrimonial por ação em ordem plausível."),
    "roe": Range(-1_000.0, 1_000.0, "ROE em percentual; acima de 1.000% é erro de unidade."),
    "dividend_yield": Range(
        0.0,
        200.0,
        "DY acima de 200% ao ano é provento extraordinário mal anualizado.",
    ),
    "debt_to_equity": Range(
        -10_000.0, 10_000.0, "Endividamento em percentual, com folga para patrimônio negativo."
    ),
    "profit_margin": Range(
        -10_000.0, 1_000.0, "Margem em percentual; acima de 1.000% é erro de unidade."
    ),
    "revenue_growth": Range(
        -100.0, 10_000.0, "Crescimento em percentual; abaixo de -100% seria receita negativa."
    ),
    "fifty_two_week_high": Range(0.01, 1_000_000.0, "Máxima de 52 semanas, mesma faixa do preço."),
    "fifty_two_week_low": Range(0.01, 1_000_000.0, "Mínima de 52 semanas, mesma faixa do preço."),
}


@dataclass
class Verdict:
    accepted: bool
    dropped: dict[str, float]
    reason: str = ""

    def as_dict(self) -> dict:
        return {"accepted": self.accepted, "dropped": self.dropped, "reason": self.reason}


def check_field(name: str, value: float | None) -> bool:
    if value is None:
        return True
    faixa = RANGES.get(name)
    return True if faixa is None else faixa.accepts(value)


def screen(values: dict[str, float | None], symbol: str = "") -> tuple[dict, Verdict]:
    clean = dict(values)
    dropped: dict[str, float] = {}

    for name, faixa in RANGES.items():
        value = clean.get(name)
        if value is None or faixa.accepts(value):
            continue

        dropped[name] = value

        if faixa.critical:
            logger.warning(
                "Snapshot de %s rejeitado: %s=%r fora da faixa [%s, %s]. %s",
                symbol or "?",
                name,
                value,
                faixa.low,
                faixa.high,
                faixa.reason,
            )
            return clean, Verdict(
                accepted=False,
                dropped=dropped,
                reason=(
                    f"{name}={value!r} fora da faixa aceita. {faixa.reason} "
                    "Sem esse campo não há veredito possível, então o dado inteiro foi recusado."
                ),
            )

        clean[name] = None

    if dropped:
        logger.info("Campos implausíveis descartados de %s: %s", symbol or "?", sorted(dropped))

    return clean, Verdict(accepted=True, dropped=dropped)


def describe_ranges() -> list[dict]:
    return [
        {
            "field": name,
            "low": faixa.low,
            "high": faixa.high,
            "reason": faixa.reason,
            "rejects_snapshot": faixa.critical,
        }
        for name, faixa in sorted(RANGES.items())
    ]
