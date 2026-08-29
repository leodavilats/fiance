from __future__ import annotations

from dataclasses import dataclass

from app.analysis.decision import (
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


@dataclass(frozen=True)
class Falsifier:
    metric: str
    condition: str
    becomes: str
    becomes_label: str
    current: float
    threshold: float
    unit: str

    def as_dict(self) -> dict:
        return {
            "metric": self.metric,
            "condition": self.condition,
            "becomes": self.becomes,
            "becomes_label": self.becomes_label,
            "current": round(self.current, 2),
            "threshold": round(self.threshold, 2),
            "unit": self.unit,
        }


def _price_at(consensus: float, mos: float) -> float:
    return consensus * (1 - mos)


def _price_falsifiers(consensus: float, price: float, verdict: str) -> list[Falsifier]:
    if verdict not in _ORDER:
        return []

    indice = _ORDER.index(verdict)
    saida: list[Falsifier] = []

    if indice > 0:
        alvo = _ORDER[indice - 1]
        alvo_preco = _price_at(consensus, _BANDS[indice - 1][0])
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
        alvo_preco = _price_at(consensus, _BANDS[indice][0])
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
    consensus: float | None,
    consensus_methods: int,
    price: float,
    avg_dividend: float | None,
) -> Falsifier | None:
    if not bazin or not consensus or not avg_dividend or consensus_methods < 1:
        return None
    if consensus <= price:
        return None

    outros = consensus * consensus_methods - bazin
    bazin_alvo = price * consensus_methods - outros
    if bazin_alvo >= bazin:
        return None
    if bazin_alvo < 0:
        return None

    corte = 1 - bazin_alvo / bazin
    dividendo_alvo = avg_dividend * bazin_alvo / bazin

    condicao = (
        "O dividendo ser suspenso por completo"
        if corte >= 0.995
        else (
            f"O dividendo médio cair {corte * 100:.0f}% "
            f"(de R$ {avg_dividend:.2f} para R$ {dividendo_alvo:.2f} por ação ao ano)"
        )
    )

    return Falsifier(
        metric="dividend",
        condition=condicao,
        becomes="HOLD",
        becomes_label=LABELS["HOLD"],
        current=avg_dividend,
        threshold=dividendo_alvo,
        unit="BRL/ação/ano",
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
) -> list[dict]:
    if not price or not consensus or verdict == "UNKNOWN":
        return []

    itens = _price_falsifiers(consensus, price, verdict)

    dividendo = _dividend_falsifier(bazin, consensus, consensus_methods, price, avg_dividend)
    if dividendo:
        itens.append(dividendo)

    tendencia = _trend_falsifier(trend, sma_50, sma_200)
    if tendencia:
        itens.append(tendencia)

    return [item.as_dict() for item in itens]
