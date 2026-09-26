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
    margin_exact,
)
from app.analysis.fii_segments import SEGMENT_PAPER
from app.analysis.texto import numero, pct, reais

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


def _margin_for_verdict(fair: FairPriceResult) -> float | None:
    if fair.price:
        return margin_exact(fair.price, fair.fair_low, fair.fair_high)
    return fair.margin_of_safety


def verdict_for(fair: FairPriceResult) -> Verdict:
    verdict = _verdict_from_mos(_margin_for_verdict(fair))
    if fair.band_quality == "fragil":
        return _CAP_WHEN_FRAGILE.get(verdict, verdict)
    return verdict


_TREND_PHRASES = {
    TREND_BASIS_LONG: {
        "up": "a média do preço nos últimos 50 dias está acima da média dos últimos 200",
        "down": "a média do preço nos últimos 50 dias está abaixo da média dos últimos 200",
    },
    TREND_BASIS_SHORT: {
        "up": (
            "a média do preço nos últimos 20 dias está acima da média dos últimos 50, com "
            "histórico curto"
        ),
        "down": (
            "a média do preço nos últimos 20 dias está abaixo da média dos últimos 50, com "
            "histórico curto"
        ),
    },
    TREND_BASIS_NONE: {
        "up": "pela média do preço no período disponível",
        "down": "pela média do preço no período disponível",
    },
}


def _trend_phrase(basis: str | None) -> dict[str, str]:
    return _TREND_PHRASES.get(basis or TREND_BASIS_NONE, _TREND_PHRASES[TREND_BASIS_NONE])


def _band_reason(fair: FairPriceResult, price: float) -> str:
    faixa = f"que vai de {reais(fair.fair_low)} a {reais(fair.fair_high)}"
    mos = fair.margin_of_safety or 0.0

    if mos > 0:
        return f"O preço está {pct(mos)} abaixo do piso da faixa de preço justo, {faixa}."
    if mos < 0:
        return (
            f"O preço está {pct(price / fair.fair_high - 1)} acima do teto da faixa de preço "
            f"justo, {faixa}."
        )

    onde = fair.band_position
    lugar = ""
    if onde is not None:
        lugar = (
            ", mais perto do piso"
            if onde <= 0.33
            else ", mais perto do teto"
            if onde >= 0.67
            else ", no meio dela"
        )
    return (
        f"O preço está dentro da faixa de preço justo, {faixa}{lugar}: não há folga a favor "
        "nem excesso contra."
    )


def _value_reason(fair: FairPriceResult) -> str:
    if fair.principal == PRINCIPAL_EARNINGS:
        return (
            f"Vale cerca de {reais(fair.principal_value)} pelo lucro que a empresa pode "
            "distribuir sem deixar de crescer."
        )
    return (
        f"Vale cerca de {reais(fair.principal_value)} pelo que o fundo distribui num ano "
        f"típico, {reais(fair.premises['dividend_recurring'])} por cota."
    )


def _rate_base(fair: FairPriceResult) -> str:
    if fair.premises.get("rate_base") == RATE_BASE_AVERAGE:
        return "a Selic média de 10 anos, o juro básico do país"
    return "a Selic do dia, o juro básico do país, sem a série de 10 anos"


def _premise_reason(fair: FairPriceResult) -> str:
    p = fair.premises
    base = _rate_base(fair)

    if fair.principal == PRINCIPAL_EARNINGS:
        texto = (
            f"Na conta, a taxa exigida — o retorno mínimo para o investimento valer a pena — é "
            f"de {pct(p['discount_rate'])} ao ano: {base}, mais 5 pontos. O lucro cresce "
            f"{pct(p['growth'])} ao ano por {p['explicit_years']} anos — o retorno sobre o "
            f"patrimônio (ROE) de {pct(p['roe'], 0)} vezes a parte do lucro que a empresa "
            f"retém — e {pct(p['long_run_growth'])} depois. A faixa cobre esse cenário e o de "
            "não crescer e distribuir todo o lucro, com 1 ponto de taxa a mais e a menos."
        )
        if p.get("growth_creates_value") is False:
            texto += (
                f" Aqui crescer consome valor: o ROE de {pct(p['roe'], 0)} não paga a taxa "
                f"exigida, e distribuindo todo o lucro a empresa valeria "
                f"{reais(p['value_without_growth'])}."
            )
        return texto

    texto = (
        f"Na conta, o rendimento exigido do fundo é de {pct(p['fii_yield'])} ao ano: o juro "
        f"real de longo prazo, que é o que sobra acima da inflação ({base}, menos a meta de "
        f"inflação de {pct(p['inflation_target'], 0)}, com piso de "
        f"{pct(p['real_rate_floor'], 0)}), mais {pct(p['fii_premium'], 0)} de prêmio pelo risco"
    )
    if p.get("fii_segment") == SEGMENT_PAPER:
        texto += (
            ", mais a meta de inflação, porque o fundo é de papel: ele vive de dívidas "
            "imobiliárias, e o que distribui já traz a correção pela inflação, sem que o valor "
            "emprestado cresça com ela"
        )
    return texto + ". A faixa vai de 1 ponto a mais a 1 ponto a menos de rendimento exigido."


_CONFIRMATION_NAME = {
    "bazin": "pelos dividendos,",
    "vpa": "pelo valor patrimonial, o patrimônio do fundo dividido pelas cotas,",
}


def _confirmation_reason(fair: FairPriceResult) -> str | None:
    c = fair.confirmation
    if not c:
        return None

    nome = _CONFIRMATION_NAME.get(c["method"], c["method"])
    valor = c["value"]
    if c["agreement"] == AGREEMENT_INSIDE:
        return f"Uma segunda conta, {nome} dá {reais(valor)}: cai dentro da faixa e a confirma."

    lado = "abaixo do piso" if valor < fair.fair_low else "acima do teto"
    referencia = fair.fair_low if valor < fair.fair_low else fair.fair_high
    return (
        f"Uma segunda conta, {nome} dá {reais(valor)}, {pct(abs(valor / referencia - 1), 0)} "
        f"{lado}: não confirma a faixa."
    )


def _personal_reason(fair: FairPriceResult, price: float | None) -> str | None:
    teto = fair.personal_ceiling
    if not teto or not price:
        return None

    meta = pct(fair.desired_yield_used, 0)
    if price <= teto:
        return (
            f"Cabe na sua meta de renda: para render os {meta} ao ano que você pediu em "
            f"proventos, o preço-teto é {reais(teto)}, e o de hoje está abaixo."
        )
    return (
        f"Não cabe na sua meta de renda: para render os {meta} ao ano que você pediu em "
        f"proventos, o preço-teto é {reais(teto)}, abaixo do de hoje."
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
        pvp = f"Preço sobre valor patrimonial (P/VP) de {numero(fair.pvp)}"
        if fair.pvp < 1:
            reasons.append(f"{pvp}: paga-se menos que o patrimônio que está no balanço.")
        elif fair.pvp > 1:
            reasons.append(f"{pvp}: paga-se mais que o patrimônio que está no balanço.")
        else:
            reasons.append(f"{pvp}: paga-se o patrimônio que está no balanço.")

    if tech:
        base = _trend_phrase(getattr(tech, "trend_basis", TREND_BASIS_NONE))

        if tech.trend == "uptrend":
            reasons.append(
                f"O preço vem subindo: {base['up']}. É contexto de preço, e não muda a leitura "
                "de valor."
            )
        elif tech.trend == "downtrend":
            reasons.append(
                f"O preço vem caindo: {base['down']}. É contexto de preço, e não muda a leitura "
                "de valor."
            )

        if tech.rsi_14 is not None:
            forca = f"o índice de força relativa (RSI) está em {tech.rsi_14:.0f}, de 0 a 100"
            if tech.rsi_14 >= 70:
                reasons.append(
                    f"O preço subiu rápido em pouco tempo: {forca}. É contexto, não leitura de "
                    "valor."
                )
            elif tech.rsi_14 <= 30:
                reasons.append(
                    f"O preço caiu rápido em pouco tempo: {forca}. É contexto, não leitura de "
                    "valor."
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
    banda = _verdict_from_mos(_margin_for_verdict(fair))
    verdict = verdict_for(fair)
    tem_principal = fair.principal in (PRINCIPAL_EARNINGS, PRINCIPAL_DIVIDENDS)

    if tem_faixa:
        if current_price:
            reasons.append(_band_reason(fair, current_price))
        else:
            reasons.append(
                f"Sem cotação: a faixa de preço justo vai de {reais(fair.fair_low)} a "
                f"{reais(fair.fair_high)}, e não há preço para comparar com ela."
            )
        if verdict != banda:
            reasons.append(
                "Com evidência frágil, a leitura não passa de "
                f"'{LABELS[verdict].lower()}', mesmo com a margem que tem."
            )
        if tem_principal:
            reasons.append(_value_reason(fair))
        confirmacao = _confirmation_reason(fair)
        if confirmacao:
            reasons.append(confirmacao)
        if fair.quality_reasons:
            reasons.append("Qualidade da faixa: " + "; ".join(fair.quality_reasons) + ".")
    else:
        reasons.append(_no_band_reason(fair))

    pessoal = _personal_reason(fair, current_price)
    if pessoal:
        reasons.append(pessoal)

    if tem_faixa and tem_principal:
        reasons.append(_premise_reason(fair))

    reasons.extend(_context_reasons(fair, tech))

    if avg_cost and current_price:
        pnl_pct = (current_price - avg_cost) / avg_cost * 100

        if pnl_pct >= 0:
            reasons.append(f"Você está com lucro de {numero(pnl_pct, 1)}% nesta posição.")
        else:
            reasons.append(f"Você está com prejuízo de {numero(abs(pnl_pct), 1)}% nesta posição.")

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
