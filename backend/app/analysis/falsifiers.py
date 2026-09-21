from __future__ import annotations

from dataclasses import dataclass

from app.analysis.decision import (
    BASIS_BAND,
    BASIS_TREND,
    LABELS,
    MOS_BUY,
    MOS_SELL,
    MOS_STRONG_BUY,
    MOS_STRONG_SELL,
)

_BANDS: tuple[tuple[float, str], ...] = (
    (MOS_STRONG_BUY, "STRONG_BUY"),
    (MOS_BUY, "BUY"),
    (MOS_SELL, "HOLD"),
    (MOS_STRONG_SELL, "SELL"),
)

_ORDER: tuple[str, ...] = tuple(nome for _, nome in _BANDS) + ("STRONG_SELL",)


KIND_TRIGGER = "gatilho"

KIND_PREMISE = "premissa"


@dataclass(frozen=True)
class Falsifier:
    metric: str
    condition: str
    becomes: str
    becomes_label: str
    current: float
    threshold: float
    unit: str
    kind: str = KIND_TRIGGER

    def as_dict(self) -> dict:
        return {
            "metric": self.metric,
            "condition": self.condition,
            "becomes": self.becomes,
            "becomes_label": self.becomes_label,
            "current": round(self.current, 2),
            "threshold": round(self.threshold, 2),
            "unit": self.unit,
            "kind": self.kind,
        }


def _price_at(fair_low: float, fair_high: float, mos: float) -> float:
    return (fair_low if mos >= 0 else fair_high) * (1 - mos)


def _price_falsifiers(
    fair_low: float, fair_high: float, price: float, verdict: str
) -> list[Falsifier]:
    if verdict not in _ORDER:
        return []

    indice = _ORDER.index(verdict)
    saida: list[Falsifier] = []

    if indice > 0:
        alvo = _ORDER[indice - 1]
        alvo_preco = _price_at(fair_low, fair_high, _BANDS[indice - 1][0])
        if alvo_preco >= price:
            return saida
        saida.append(
            Falsifier(
                metric="price",
                condition=f"O preço cair para R$ {alvo_preco:.2f} ou menos",
                becomes=alvo,
                becomes_label=LABELS.get(alvo, alvo),
                current=price,
                threshold=alvo_preco,
                unit="BRL",
            )
        )

    if indice < len(_ORDER) - 1:
        alvo = _ORDER[indice + 1]
        alvo_preco = _price_at(fair_low, fair_high, _BANDS[indice][0])
        if alvo_preco <= price:
            return saida
        saida.append(
            Falsifier(
                metric="price",
                condition=f"O preço subir para R$ {alvo_preco:.2f} ou mais",
                becomes=alvo,
                becomes_label=LABELS.get(alvo, alvo),
                current=price,
                threshold=alvo_preco,
                unit="BRL",
            )
        )

    return saida


def _dividend_falsifier(
    bazin: float | None,
    price: float,
    avg_dividend: float | None,
) -> Falsifier | None:
    if not bazin or not avg_dividend or bazin <= price:
        return None

    corte = 1 - price / bazin
    dividendo_alvo = avg_dividend * price / bazin

    condicao = (
        "O dividendo ser suspenso por completo"
        if corte >= 0.995
        else (
            f"O dividendo médio cair {corte * 100:.0f}% "
            f"(de R$ {avg_dividend:.2f} para R$ {dividendo_alvo:.2f} por ação ao ano) — aí o "
            "preço de hoje deixa de ser justificado pela distribuição"
        )
    )

    return Falsifier(
        metric="dividend",
        condition=condicao,
        becomes="REVIEW",
        becomes_label="Rever a tese",
        current=avg_dividend,
        threshold=dividendo_alvo,
        unit="BRL/ação/ano",
        kind=KIND_PREMISE,
    )


def _growth_falsifier(
    dcf: float | None,
    dcf_sem_crescimento: float | None,
    price: float,
) -> Falsifier | None:
    if not dcf or not dcf_sem_crescimento or dcf_sem_crescimento >= dcf:
        return None
    if dcf_sem_crescimento >= price:
        return None

    queda = 1 - dcf_sem_crescimento / dcf

    return Falsifier(
        metric="growth",
        condition=(
            f"O crescimento projetado não se confirmar: sem ele, os lucros descontados valem "
            f"R$ {dcf_sem_crescimento:.2f} em vez de R$ {dcf:.2f}, {queda * 100:.0f}% menos, e "
            "ficam abaixo do preço de hoje"
        ),
        becomes="REVIEW",
        becomes_label="Rever a tese",
        current=dcf,
        threshold=dcf_sem_crescimento,
        unit="BRL",
        kind=KIND_PREMISE,
    )


def _trend_falsifier(trend: str, sma_50: float | None, sma_200: float | None) -> Falsifier | None:
    if trend not in ("uptrend", "downtrend") or not sma_50 or not sma_200:
        return None

    lado = "abaixo" if trend == "uptrend" else "acima"
    condicao = f"A média de 50 dias (R$ {sma_50:.2f}) cruzar {lado} da de 200 (R$ {sma_200:.2f})"

    return Falsifier(
        metric="trend",
        condition=condicao,
        becomes="REVIEW",
        becomes_label="Rever a tese",
        current=sma_50,
        threshold=sma_200,
        unit="BRL",
    )


def momentum_falsifiers(trend: str, rsi_14: float | None) -> list[dict]:
    itens: list[Falsifier] = []

    if trend in ("uptrend", "downtrend"):
        lado = "de alta" if trend == "uptrend" else "de baixa"
        contrario = "de baixa" if trend == "uptrend" else "de alta"
        itens.append(
            Falsifier(
                metric="trend",
                condition=f"A tendência {lado} virar {contrario}",
                becomes="REVIEW",
                becomes_label="Rever a tese",
                current=0.0,
                threshold=0.0,
                unit="",
            )
        )

    if rsi_14 is not None:
        alvo = 70.0 if rsi_14 < 70 else 30.0
        sentido = "passar de" if rsi_14 < 70 else "cair abaixo de"
        itens.append(
            Falsifier(
                metric="rsi",
                condition=f"O RSI {sentido} {alvo:.0f}",
                becomes="REVIEW",
                becomes_label="Rever a tese",
                current=rsi_14,
                threshold=alvo,
                unit="pontos",
            )
        )

    return [item.as_dict() for item in itens]


def falsifiers(
    verdict: str,
    price: float | None,
    consensus: float | None,
    bazin: float | None = None,
    consensus_methods: int = 0,
    avg_dividend: float | None = None,
    trend: str = "unknown",
    sma_50: float | None = None,
    sma_200: float | None = None,
    rsi_14: float | None = None,
    band_verdict: str | None = None,
    fair_low: float | None = None,
    fair_high: float | None = None,
    basis: str = BASIS_BAND,
    dcf: float | None = None,
    dcf_sem_crescimento: float | None = None,
) -> list[dict]:
    if not price or verdict == "UNKNOWN":
        return []

    if basis == BASIS_TREND:
        return momentum_falsifiers(trend, rsi_14)

    if fair_low is None or fair_high is None:
        return []

    banda = band_verdict or verdict

    itens = _price_falsifiers(fair_low, fair_high, price, banda)

    tendencia = _trend_falsifier(trend, sma_50, sma_200)
    if tendencia:
        itens.append(tendencia)

    dividendo = _dividend_falsifier(bazin, price, avg_dividend)
    if dividendo:
        itens.append(dividendo)

    crescimento = _growth_falsifier(dcf, dcf_sem_crescimento, price)
    if crescimento:
        itens.append(crescimento)

    return [item.as_dict() for item in itens]
