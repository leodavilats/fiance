from __future__ import annotations

from dataclasses import dataclass

from app.analysis.decision import (
    BASIS_BAND,
    LABELS,
    MOS_BUY,
    MOS_SELL,
    MOS_STRONG_BUY,
    MOS_STRONG_SELL,
)
from app.analysis.fair_price import PRINCIPAL_DIVIDENDS, PRINCIPAL_EARNINGS, FairPriceResult

_BANDS: tuple[tuple[float, str], ...] = (
    (MOS_STRONG_BUY, "STRONG_BUY"),
    (MOS_BUY, "BUY"),
    (MOS_SELL, "HOLD"),
    (MOS_STRONG_SELL, "SELL"),
)

_BANDS_FRAGILE: tuple[tuple[float, str], ...] = (
    (MOS_BUY, "BUY"),
    (MOS_SELL, "HOLD"),
)


def _order(bands: tuple[tuple[float, str], ...]) -> tuple[str, ...]:
    ultimo = "STRONG_SELL" if bands[-1][1] == "SELL" else "SELL"
    return tuple(nome for _, nome in bands) + (ultimo,)


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
            "current": round(self.current, 4),
            "threshold": round(self.threshold, 4),
            "unit": self.unit,
            "kind": self.kind,
        }


def price_at_margin(fair_low: float, fair_high: float, mos: float) -> float:
    return fair_low * (1 - mos) if mos >= 0 else fair_high / (1 + mos)


def _price_falsifiers(
    fair_low: float, fair_high: float, price: float, verdict: str, fragile: bool
) -> list[Falsifier]:
    bands = _BANDS_FRAGILE if fragile else _BANDS
    order = _order(bands)
    if verdict not in order:
        return []

    indice = order.index(verdict)
    saida: list[Falsifier] = []

    if indice > 0:
        alvo = order[indice - 1]
        alvo_preco = price_at_margin(fair_low, fair_high, bands[indice - 1][0])
        if alvo_preco < price:
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

    if indice < len(order) - 1:
        alvo = order[indice + 1]
        alvo_preco = price_at_margin(fair_low, fair_high, bands[indice][0])
        if alvo_preco > price:
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


def _growth_falsifier(fair: FairPriceResult, price: float) -> Falsifier | None:
    p = fair.premises
    sem_crescimento = p.get("value_without_growth")
    crescimento = p.get("growth") or 0.0
    if not sem_crescimento or crescimento <= 0 or not fair.consensus:
        return None
    if sem_crescimento >= fair.consensus:
        return None
    if not (sem_crescimento < price <= fair.fair_high):
        return None

    return Falsifier(
        metric="growth",
        condition=(
            f"O crescimento de {crescimento * 100:.1f}% ao ano não se confirmar: sem ele, o "
            f"valor cai de R$ {fair.consensus:.2f} para R$ {sem_crescimento:.2f}, abaixo do "
            "preço de hoje"
        ),
        becomes="REVIEW",
        becomes_label="Rever a tese",
        current=crescimento,
        threshold=0.0,
        unit="fração ao ano",
        kind=KIND_PREMISE,
    )


def _rate_falsifier(fair: FairPriceResult, price: float) -> Falsifier | None:
    p = fair.premises
    equilibrio = p.get("breakeven_discount_rate")
    taxa = p.get("discount_rate")
    if not equilibrio or not taxa or abs(equilibrio - taxa) < 0.001:
        return None

    if equilibrio > taxa:
        condicao = (
            f"A taxa exigida subir de {taxa * 100:.1f}% para {equilibrio * 100:.1f}%: aí o "
            "preço de hoje deixa de ter folga sobre o valor"
        )
    else:
        condicao = (
            f"A taxa exigida cair de {taxa * 100:.1f}% para {equilibrio * 100:.1f}%: aí o preço "
            "de hoje passa a ser justificado"
        )

    return Falsifier(
        metric="discount_rate",
        condition=condicao,
        becomes="REVIEW",
        becomes_label="Rever a tese",
        current=taxa,
        threshold=equilibrio,
        unit="fração ao ano",
        kind=KIND_PREMISE,
    )


def _dividend_falsifier(fair: FairPriceResult, price: float) -> Falsifier | None:
    valor = fair.consensus
    dividendo = fair.premises.get("dividend_recurring")
    if not valor or not dividendo or valor <= price:
        return None

    corte = 1 - price / valor
    dividendo_alvo = dividendo * price / valor

    condicao = (
        "A distribuição ser suspensa por completo"
        if corte >= 0.995
        else (
            f"A distribuição recorrente cair {corte * 100:.0f}% "
            f"(de R$ {dividendo:.2f} para R$ {dividendo_alvo:.2f} por cota ao ano) — aí o "
            "preço de hoje deixa de ser justificado por ela"
        )
    )

    return Falsifier(
        metric="dividend",
        condition=condicao,
        becomes="REVIEW",
        becomes_label="Rever a tese",
        current=dividendo,
        threshold=dividendo_alvo,
        unit="BRL/cota/ano",
        kind=KIND_PREMISE,
    )


def falsifiers(
    fair: FairPriceResult,
    verdict: str,
    price: float | None,
    basis: str = BASIS_BAND,
) -> list[dict]:
    if not price or verdict == "UNKNOWN" or basis != BASIS_BAND:
        return []
    if fair.fair_low is None or fair.fair_high is None:
        return []

    itens = _price_falsifiers(
        fair.fair_low, fair.fair_high, price, verdict, fair.band_quality == "fragil"
    )

    if fair.principal == PRINCIPAL_EARNINGS:
        premissas = (_growth_falsifier(fair, price), _rate_falsifier(fair, price))
    elif fair.principal == PRINCIPAL_DIVIDENDS:
        premissas = (_dividend_falsifier(fair, price),)
    else:
        premissas = ()

    itens.extend(p for p in premissas if p)
    return [item.as_dict() for item in itens]
