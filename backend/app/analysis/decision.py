from __future__ import annotations

from dataclasses import dataclass, field

from app.analysis.fair_price import FairPriceResult, TechnicalSnapshot

MOS_STRONG_BUY = 0.30

MOS_BUY = 0.15

MOS_SELL = -0.15

MOS_STRONG_SELL = -0.30

Verdict = str


@dataclass
class Decision:
    verdict: Verdict

    label: str

    confidence: float

    reasons: list[str] = field(default_factory=list)


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


_LABELS = {
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

    confidence = 0.4

    if fair.consensus and current_price:
        if fair.margin_of_safety is not None:
            mos_pct = fair.margin_of_safety * 100

            if mos_pct > 0:
                reasons.append(
                    f"Preço atual está {mos_pct:.1f}% abaixo do preço justo estimado "
                    f"(R$ {fair.consensus:.2f})."
                )

            else:
                reasons.append(
                    f"Preço atual está {abs(mos_pct):.1f}% acima do preço justo estimado "
                    f"(R$ {fair.consensus:.2f})."
                )

        confidence += 0.2

    if fair.bazin:
        reasons.append(f"Preço justo Bazin (dividendos): R$ {fair.bazin:.2f}.")

    if fair.graham:
        reasons.append(f"Preço justo Graham (lucro/PL): R$ {fair.graham:.2f}.")

    if tech:
        if tech.trend == "uptrend":
            reasons.append("Tendência de alta (média 50 acima da 200).")

            if verdict in ("HOLD", "SELL"):
                confidence += 0.1

        elif tech.trend == "downtrend":
            reasons.append("Tendência de baixa (média 50 abaixo da 200).")

            if verdict in ("BUY", "STRONG_BUY"):
                verdict = "HOLD" if verdict == "BUY" else "BUY"

                reasons.append("Apesar do desconto, evite entrar contra a tendência principal.")

            elif verdict == "HOLD":
                verdict = "SELL"

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
        label=_LABELS.get(verdict, "Manter"),
        confidence=confidence,
        reasons=reasons,
    )
