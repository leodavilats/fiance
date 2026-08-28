"""Faixa de plausibilidade por campo do dado externo.

A validação de hoje é por **tipo** (`_safe_float`), não por **magnitude**: um
ROE de 12.000% ou um preço de R$ 0,0001 passam, entram no cálculo e viram
patrimônio. Dado errado em produto pago é a reclamação número 1 dos
concorrentes brasileiros — e o modo de falha aqui é o pior possível, porque o
número absurdo não gera erro, gera um veredito.

Duas severidades, e a diferença é deliberada:

* **Campo implausível vira `None`.** O produto já sabe conviver com indicador
  ausente — a régua de score baixa a confiança e a tela diz que falta dado.
  Continuar com o número errado é que não tem defesa.
* **Preço implausível rejeita o snapshot inteiro.** Sem preço não há posição,
  patrimônio nem veredito; aceitar o resto seria montar uma tela inteira sobre
  o campo que falhou.

Os limites são largos de propósito. O alvo é o absurdo — erro de unidade, campo
trocado, valor sentinela —, não o extremo legítimo: a B3 tem empresa com ROE de
80% e ação de R$ 0,90, e rejeitá-las seria trocar um erro por outro.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("fiance.plausibility")


@dataclass(frozen=True)
class Range:
    """Faixa aceita de um campo, com o motivo do limite."""

    low: float
    high: float
    reason: str
    #: Quando verdadeiro, valor fora da faixa invalida o snapshot inteiro em vez
    #: de apenas zerar o campo.
    critical: bool = False

    def accepts(self, value: float) -> bool:
        return self.low <= value <= self.high


#: Faixa por campo do `AssetSnapshot`. Campo ausente daqui não é verificado —
#: a lista é explícita para que adicionar um campo seja uma decisão, e não um
#: esquecimento silencioso.
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
    # Os quatro abaixo chegam em **percentual** (ver `_ratio_to_pct`). Um valor
    # de 2.039 aqui é o sinal clássico de dupla conversão.
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
    """O que sobrou do snapshot, e o que foi descartado."""

    accepted: bool
    dropped: dict[str, float]
    reason: str = ""

    def as_dict(self) -> dict:
        return {"accepted": self.accepted, "dropped": self.dropped, "reason": self.reason}


def check_field(name: str, value: float | None) -> bool:
    """`True` quando o campo é aceitável — ou quando não há faixa declarada."""
    if value is None:
        return True
    faixa = RANGES.get(name)
    return True if faixa is None else faixa.accepts(value)


def screen(values: dict[str, float | None], symbol: str = "") -> tuple[dict, Verdict]:
    """Filtra os campos implausíveis e diz se o snapshot ainda serve.

    Devolve uma cópia dos valores: o dicionário de entrada não é mutado, porque
    quem chama costuma querer registrar o original ao lado do que sobrou.
    """
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
    """As faixas publicadas — o `/data-quality` mostra o que está sendo cobrado."""
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
