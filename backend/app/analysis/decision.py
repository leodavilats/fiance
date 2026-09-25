from __future__ import annotations

from dataclasses import dataclass, field

from app.analysis.fair_price import (
    AGREEMENT_INSIDE,
    PRINCIPAL_DIVIDENDS,
    PRINCIPAL_EARNINGS,
    RATE_BASE_AVERAGE,
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
    "fragil": 0.30,
    "sem_faixa": 0.0,
}

CONFIDENCE_LABELS = ((0.6, "alta"), (0.4, "média"), (0.0, "baixa"))

BASIS_BAND = "band"

BASIS_NONE = "none"

Verdict = str

LABELS = {
    "STRONG_BUY": "Bem abaixo do preço justo",
    "BUY": "Abaixo do preço justo",
    "HOLD": "No preço justo",
    "SELL": "Acima do preço justo",
    "STRONG_SELL": "Bem acima do preço justo",
    "UNKNOWN": "Sem preço justo",
}

LABEL_NO_QUOTE = "Sem cotação"

_CAP_WHEN_FRAGILE = {"STRONG_BUY": "BUY", "STRONG_SELL": "SELL"}


def confidence_from_evidence(fair: FairPriceResult, basis: str) -> float:
    if basis != BASIS_BAND or fair.margin_of_safety is None:
        return 0.0
    return CONFIDENCE_BY_QUALITY.get(fair.band_quality, 0.0)


def confidence_label(confidence: float) -> str:
    for piso, rotulo in CONFIDENCE_LABELS:
        if confidence >= piso:
            return rotulo
    return "baixa"


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


def verdict_for(fair: FairPriceResult) -> Verdict:
    verdict = _verdict_from_mos(fair.margin_of_safety)
    if fair.band_quality == "fragil":
        return _CAP_WHEN_FRAGILE.get(verdict, verdict)
    return verdict


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


def _pct(valor: float, casas: int = 1) -> str:
    return f"{valor * 100:.{casas}f}%"


def _brl(valor: float | None) -> str:
    return f"R$ {valor or 0:.2f}"


def _band_reason(fair: FairPriceResult, price: float) -> str:
    faixa = f"{_brl(fair.fair_low)} a {_brl(fair.fair_high)}"
    mos = fair.margin_of_safety or 0.0

    if mos > 0:
        return f"O preço está {_pct(mos)} abaixo do piso da faixa de preço justo ({faixa})."
    if mos < 0:
        return (
            f"O preço está {_pct(price / fair.fair_high - 1)} acima do teto da faixa de preço "
            f"justo ({faixa})."
        )

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
    return (
        f"O preço está dentro da faixa de preço justo ({faixa}): não há margem a favor nem "
        f"contra{lugar}."
    )


def _premise_reason(fair: FairPriceResult) -> str:
    p = fair.premises
    base = (
        "Selic média de 10 anos"
        if p.get("rate_base") == RATE_BASE_AVERAGE
        else "Selic do dia, sem a série de 10 anos"
    )

    if fair.principal == PRINCIPAL_EARNINGS:
        return (
            f"Vale cerca de {_brl(fair.consensus)} pelo lucro que a empresa pode distribuir sem "
            f"deixar de crescer: taxa exigida de {_pct(p['discount_rate'])} ({base} mais 5 "
            f"pontos), crescimento de {_pct(p['growth'])} ao ano por {p['explicit_years']} anos "
            f"— o ROE de {_pct(p['roe'], 0)} vezes o que ela retém — e "
            f"{_pct(p['long_run_growth'])} depois. A faixa vai do cenário sem crescimento e "
            "com 1 ponto a mais de taxa ao cenário com crescimento e 1 ponto a menos."
        )

    return (
        f"Vale cerca de {_brl(fair.consensus)} pela distribuição recorrente de "
        f"{_brl(p['dividend_recurring'])} por cota ao ano, exigindo yield de "
        f"{_pct(p['fii_yield'])}: o juro real de longo prazo ({base} menos a meta de inflação "
        f"de {_pct(p['inflation_target'], 0)}, com piso de {_pct(p['real_rate_floor'], 0)}) mais "
        f"{_pct(p['fii_premium'], 0)} de prêmio. A faixa vai de 1 ponto a mais a 1 ponto a menos "
        "de yield."
    )


_CONFIRMATION_NAME = {"bazin": "Pelos dividendos", "vpa": "Pelo valor patrimonial"}


def _confirmation_reason(fair: FairPriceResult) -> str | None:
    c = fair.confirmation
    if not c:
        return None

    nome = _CONFIRMATION_NAME.get(c["method"], c["method"])
    valor = c["value"]
    if c["agreement"] == AGREEMENT_INSIDE:
        return f"{nome}, {_brl(valor)}: dentro da faixa, e a confirma por outro insumo."

    lado = "abaixo do piso" if valor < fair.fair_low else "acima do teto"
    referencia = fair.fair_low if valor < fair.fair_low else fair.fair_high
    return (
        f"{nome}, {_brl(valor)}: {_pct(abs(valor / referencia - 1), 0)} {lado}. A outra leitura "
        "não confirma a faixa."
    )


def _personal_reason(fair: FairPriceResult, price: float | None) -> str | None:
    teto = fair.personal_ceiling
    if not teto or not price:
        return None

    meta = _pct(fair.desired_yield_used, 0)
    if price <= teto:
        return (
            f"Cabe na sua meta de renda: para render os {meta} que você pediu, o preço-teto é "
            f"{_brl(teto)}, e o de hoje está abaixo."
        )
    return (
        f"Não cabe na sua meta de renda: para render os {meta} que você pediu, o preço-teto é "
        f"{_brl(teto)}, abaixo do de hoje."
    )


def _no_band_reason(fair: FairPriceResult) -> str:
    principal = next(
        (m for m in fair.methods if m.get("role") in ("principal", "inaplicavel")), None
    )
    motivo = principal["note"] if principal and principal.get("note") else "falta o dado"
    return f"Não há preço justo para este ativo: {motivo}."


def _context_reasons(fair: FairPriceResult, tech: TechnicalSnapshot | None) -> list[str]:
    reasons: list[str] = []

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
                reasons.append(
                    f"RSI {tech.rsi_14:.0f}: o preço subiu rápido — contexto, não leitura de valor."
                )
            elif tech.rsi_14 <= 30:
                reasons.append(
                    f"RSI {tech.rsi_14:.0f}: o preço caiu rápido — contexto, não leitura de valor."
                )

    return reasons


def decide(
    fair: FairPriceResult,
    tech: TechnicalSnapshot | None = None,
    current_price: float | None = None,
    avg_cost: float | None = None,
) -> Decision:
    reasons: list[str] = []

    tem_faixa = fair.fair_low is not None and fair.fair_high is not None
    basis = BASIS_BAND if tem_faixa else BASIS_NONE
    banda = _verdict_from_mos(fair.margin_of_safety)
    verdict = verdict_for(fair)

    if tem_faixa:
        if current_price:
            reasons.append(_band_reason(fair, current_price))
        else:
            reasons.append(
                f"Sem cotação: a faixa de preço justo é de {_brl(fair.fair_low)} a "
                f"{_brl(fair.fair_high)}, e não há preço para comparar com ela."
            )
        if fair.principal in (PRINCIPAL_EARNINGS, PRINCIPAL_DIVIDENDS):
            reasons.append(_premise_reason(fair))
        confirmacao = _confirmation_reason(fair)
        if confirmacao:
            reasons.append(confirmacao)
        if fair.quality_reasons:
            reasons.append("Qualidade da faixa: " + "; ".join(fair.quality_reasons) + ".")
        if verdict != banda:
            reasons.append(
                "Com evidência frágil, a leitura não passa de "
                f"'{LABELS[verdict].lower()}', mesmo com a margem que tem."
            )
    else:
        reasons.append(_no_band_reason(fair))

    pessoal = _personal_reason(fair, current_price)
    if pessoal:
        reasons.append(pessoal)

    reasons.extend(_context_reasons(fair, tech))

    if avg_cost and current_price:
        pnl_pct = (current_price - avg_cost) / avg_cost * 100

        if pnl_pct >= 0:
            reasons.append(f"Você está com lucro de {pnl_pct:.1f}% nesta posição.")
        else:
            reasons.append(f"Você está com prejuízo de {abs(pnl_pct):.1f}% nesta posição.")

        if fair.margin_of_safety is not None and fair.margin_of_safety < MOS_SELL and pnl_pct > 30:
            reasons.append(
                "O preço está acima da faixa de preço justo e a posição já acumula mais de 30% "
                "de lucro."
            )

    confidence = confidence_from_evidence(fair, basis)

    return Decision(
        verdict=verdict,
        label=LABEL_NO_QUOTE if tem_faixa and verdict == "UNKNOWN" else LABELS[verdict],
        confidence=confidence,
        reasons=reasons,
        band_verdict=banda,
        basis=basis,
    )
