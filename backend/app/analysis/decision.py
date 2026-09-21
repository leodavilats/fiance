from __future__ import annotations

from dataclasses import dataclass, field

from app.analysis.fair_price import (
    TREND_BASIS_LONG,
    TREND_BASIS_NONE,
    TREND_BASIS_SHORT,
    FairPriceResult,
    TechnicalSnapshot,
)

MOS_STRONG_BUY = 0.30

MOS_BUY = 0.15

MOS_SELL = -0.15

MOS_STRONG_SELL = -0.30

CONFIDENCE_BY_QUALITY = {
    "firme": 0.70,
    "ampla": 0.45,
    "fragil": 0.35,
    "sem_faixa": 0.0,
}

CONFIDENCE_TREND_ONLY = 0.25

CONFIDENCE_LABELS = ((0.6, "alta"), (0.4, "média"), (0.0, "baixa"))


def confidence_from_evidence(fair: FairPriceResult, basis: str) -> float:
    if basis == BASIS_TREND:
        return CONFIDENCE_TREND_ONLY
    if basis != BASIS_BAND:
        return 0.0

    valor = CONFIDENCE_BY_QUALITY.get(fair.band_quality, 0.35)

    if fair.independent_inputs >= 3:
        valor += 0.10

    bazin_participa = any(
        m["method"] == "bazin" and m["status"] == "ok" for m in (fair.methods or [])
    )
    if bazin_participa and fair.data_years < 3:
        valor -= 0.10

    return round(max(0.05, min(0.95, valor)), 2)


def confidence_label(confidence: float) -> str:
    for piso, rotulo in CONFIDENCE_LABELS:
        if confidence >= piso:
            return rotulo
    return "baixa"


BASIS_BAND = "band"

BASIS_TREND = "trend"

BASIS_NONE = "none"

Verdict = str


@dataclass
class Decision:
    verdict: Verdict

    label: str

    confidence: float

    reasons: list[str] = field(default_factory=list)

    band_verdict: Verdict = "UNKNOWN"

    basis: str = BASIS_BAND


def _verdict_from_mos(mos: float | None) -> Verdict:

    if mos is None:
        return "UNKNOWN"

    if mos >= MOS_STRONG_BUY:
        return "STRONG_BUY"

    if mos >= MOS_BUY:
        return "BUY"

    if mos <= MOS_STRONG_SELL:
        return "STRONG_SELL"

    if mos <= MOS_SELL:
        return "SELL"

    return "HOLD"


_TREND_PHRASES = {
    TREND_BASIS_LONG: {
        "up": "média de 50 dias acima da de 200",
        "down": "média de 50 dias abaixo da de 200",
    },
    TREND_BASIS_SHORT: {
        "up": "média de 20 dias acima da de 50, histórico curto",
        "down": "média de 20 dias abaixo da de 50, histórico curto",
    },
    TREND_BASIS_NONE: {
        "up": "médias móveis do período disponível",
        "down": "médias móveis do período disponível",
    },
}


def _trend_phrase(basis: str | None) -> dict[str, str]:
    return _TREND_PHRASES.get(basis or TREND_BASIS_NONE, _TREND_PHRASES[TREND_BASIS_NONE])


def _verdict_from_trend(tech: TechnicalSnapshot) -> tuple[Verdict, str]:
    rsi = tech.rsi_14
    if rsi is None:
        return "UNKNOWN", ""

    base = _trend_phrase(getattr(tech, "trend_basis", TREND_BASIS_NONE))

    if tech.trend == "uptrend" and rsi < 70:
        return "BUY", f"A leitura sai da tendência de alta ({base['up']}), com RSI {rsi:.0f}."

    if tech.trend == "downtrend" and rsi > 30:
        return "SELL", f"A leitura sai da tendência de baixa ({base['down']}), com RSI {rsi:.0f}."

    if rsi <= 30:
        return "BUY", f"A leitura sai do RSI {rsi:.0f}: o ativo está sobrevendido."

    if rsi >= 70:
        return "HOLD", f"A leitura sai do RSI {rsi:.0f}: o ativo está sobrecomprado."

    return "HOLD", f"Sem tendência definida e com RSI {rsi:.0f}, a leitura é manter."


LABELS = {
    "STRONG_BUY": "Comprar com convicção",
    "BUY": "Comprar",
    "HOLD": "Manter",
    "SELL": "Vender",
    "STRONG_SELL": "Vender com urgência",
    "UNKNOWN": "Sem dados suficientes",
}


def _quality_reason(fair: FairPriceResult) -> str:
    metodos = fair.consensus_methods
    insumos = fair.independent_inputs

    if fair.band_quality == "fragil" and metodos <= 1:
        return "A faixa vem de um método só: é uma estimativa pontual, e não uma convergência."
    if fair.band_quality == "fragil":
        return (
            f"Os {metodos} métodos da faixa leem o mesmo insumo, então concordar entre si não "
            "confirma nada — se o insumo estiver errado, os dois erram juntos."
        )
    if fair.band_quality == "ampla":
        return (
            f"Os {metodos} métodos variam {fair.method_dispersion:.1f}x entre si, sobre "
            f"{insumos} insumos diferentes: a faixa é larga porque o que cada um mede é "
            "diferente."
        )
    return f"A faixa se apoia em {insumos} insumos independentes, e os métodos convergem."


def decide(
    fair: FairPriceResult,
    tech: TechnicalSnapshot | None = None,
    current_price: float | None = None,
    avg_cost: float | None = None,
) -> Decision:

    reasons: list[str] = []

    verdict = _verdict_from_mos(fair.margin_of_safety)
    banda = verdict

    tem_faixa = fair.fair_low is not None and fair.fair_high is not None
    basis = BASIS_BAND if tem_faixa else BASIS_NONE

    if tem_faixa and current_price:
        faixa = f"R$ {fair.fair_low:.2f} a R$ {fair.fair_high:.2f}"
        mos = fair.margin_of_safety or 0.0

        if mos > 0:
            reasons.append(
                f"Preço atual está {mos * 100:.1f}% abaixo do piso da faixa de preço justo "
                f"({faixa})."
            )
        elif mos < 0:
            reasons.append(
                f"Preço atual está {abs(mos) * 100:.1f}% acima do teto da faixa de preço justo "
                f"({faixa})."
            )
        else:
            onde = fair.band_position
            lugar = ""
            if onde is not None:
                lugar = (
                    " — mais perto do piso"
                    if onde <= 0.33
                    else " — mais perto do teto"
                    if onde >= 0.67
                    else " — no meio dela"
                )
            reasons.append(
                f"Preço atual está dentro da faixa de preço justo ({faixa}): não há margem a "
                f"favor nem contra{lugar}."
            )

        reasons.append(_quality_reason(fair))

    if not tem_faixa and tech is not None:
        verdict, motivo = _verdict_from_trend(tech)
        if verdict != "UNKNOWN":
            basis = BASIS_TREND
            reasons.append(
                "Nenhum método de preço justo se aplica a este ativo: sem lucro, patrimônio ou "
                "dividendo que os sustentem, não há faixa."
            )
            reasons.append(motivo)

            return Decision(
                verdict=verdict,
                label=LABELS.get(verdict, "Manter"),
                confidence=confidence_from_evidence(fair, basis),
                reasons=reasons,
                band_verdict=banda,
                basis=basis,
            )

    if fair.bazin:
        reasons.append(f"Preço justo Bazin (dividendos): R$ {fair.bazin:.2f}.")

    if fair.graham:
        reasons.append(f"Preço justo Graham (lucro/PL): R$ {fair.graham:.2f}.")

    if fair.pvp:
        if fair.pvp < 1:
            reasons.append(
                f"P/VP {fair.pvp:.2f}: negociando abaixo do valor patrimonial (desconto)."
            )
        elif fair.pvp > 1:
            reasons.append(f"P/VP {fair.pvp:.2f}: negociando acima do valor patrimonial (ágio).")
        else:
            reasons.append(f"P/VP {fair.pvp:.2f}: no valor patrimonial.")

    if tech:
        base = _trend_phrase(getattr(tech, "trend_basis", TREND_BASIS_NONE))

        if tech.trend == "uptrend":
            reasons.append(
                f"Tendência de alta ({base['up']}) — é contexto de preço, e não muda a leitura "
                "de valor."
            )
        elif tech.trend == "downtrend":
            reasons.append(
                f"Tendência de baixa ({base['down']}) — é contexto de preço, e não muda a "
                "leitura de valor."
            )

        if tech.rsi_14 is not None:
            if tech.rsi_14 >= 70:
                reasons.append(f"RSI {tech.rsi_14:.0f}: ativo sobrecomprado (risco de correção).")
            elif tech.rsi_14 <= 30:
                reasons.append(
                    f"RSI {tech.rsi_14:.0f}: ativo sobrevendido (possível ponto de entrada)."
                )

    if avg_cost and current_price:
        pnl_pct = (current_price - avg_cost) / avg_cost * 100

        if pnl_pct >= 0:
            reasons.append(f"Você está com lucro de {pnl_pct:.1f}% nesta posição.")

        else:
            reasons.append(f"Você está com prejuízo de {abs(pnl_pct):.1f}% nesta posição.")

        if fair.margin_of_safety is not None and fair.margin_of_safety < MOS_SELL and pnl_pct > 30:
            reasons.append(
                "Considere realizar parte do lucro: o ativo está caro e você já lucrou bastante."
            )

    confidence = confidence_from_evidence(fair, basis)

    return Decision(
        verdict=verdict,
        label=LABELS.get(verdict, "Manter"),
        confidence=confidence,
        reasons=reasons,
        band_verdict=banda,
        basis=basis,
    )
