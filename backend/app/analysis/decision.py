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

    confidence = 0.4

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
            reasons.append(
                f"Preço atual está dentro da faixa de preço justo ({faixa}): não há margem a "
                "favor nem contra."
            )

        confidence += 0.2

        if getattr(fair, "methods_disagree", False) and fair.method_dispersion:
            reasons.append(
                f"Os {fair.consensus_methods} métodos variam {fair.method_dispersion:.1f}x entre "
                "si, e é por isso que o preço justo sai como faixa: o que cada um mede é "
                "diferente."
            )
            confidence -= 0.1

    if not tem_faixa and tech is not None:
        verdict, motivo = _verdict_from_trend(tech)
        if verdict != "UNKNOWN":
            basis = BASIS_TREND
            reasons.append(
                "Nenhum método de preço justo se aplica a este ativo: sem lucro, patrimônio ou "
                "dividendo que os sustentem, não há faixa."
            )
            reasons.append(motivo)
            confidence = 0.35

            return Decision(
                verdict=verdict,
                label=LABELS.get(verdict, "Manter"),
                confidence=confidence,
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
            reasons.append(f"Tendência de alta ({base['up']}).")

            if verdict in ("HOLD", "SELL"):
                confidence += 0.1

        elif tech.trend == "downtrend":
            reasons.append(f"Tendência de baixa ({base['down']}).")

            if verdict in ("BUY", "STRONG_BUY"):
                anterior = LABELS[verdict]
                verdict = "HOLD" if verdict == "BUY" else "BUY"

                reasons.append(
                    f"O preço está descontado, mas a tendência principal é de queda: a leitura "
                    f"cai de {anterior.lower()} para {LABELS[verdict].lower()}."
                )

            elif verdict == "HOLD":
                verdict = "SELL"
                reasons.append(
                    "O desconto não chega à faixa que pede compra, e a tendência principal é de "
                    "queda: a leitura cai para vender."
                )

        if tech.rsi_14 is not None:
            if tech.rsi_14 >= 70:
                reasons.append(f"RSI {tech.rsi_14:.0f}: ativo sobrecomprado (risco de correção).")

                if verdict == "BUY":
                    verdict = "HOLD"

            elif tech.rsi_14 <= 30:
                reasons.append(
                    f"RSI {tech.rsi_14:.0f}: ativo sobrevendido (possível ponto de entrada)."
                )

                if verdict == "HOLD":
                    verdict = "BUY"

        confidence += 0.15

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

    confidence = min(0.95, round(confidence, 2))

    return Decision(
        verdict=verdict,
        label=LABELS.get(verdict, "Manter"),
        confidence=confidence,
        reasons=reasons,
        band_verdict=banda,
        basis=basis,
    )
