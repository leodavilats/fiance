"""O que faria a tese mudar.

Um veredito sem condição de queda é fé. "Comprar" com as razões ao lado explica
como se chegou ali, mas não diz o que precisaria acontecer para deixar de valer
— e sem isso a pessoa não tem como acompanhar a tese, só como torcer por ela.

O que este módulo produz não é opinião nova: é a **mesma régua lida ao
contrário**. Os limiares de margem de segurança que definem o veredito também
definem, por álgebra, o preço em que ele muda. O preço justo de Bazin sai do
dividendo, então o corte de dividendo que derruba a tese também sai da conta.

Por isso não há falsificador genérico aqui. Se a conta não fecha — sem preço
justo, sem consenso, sem dividendo — nenhum item é emitido. Um "fique de olho
nos resultados trimestrais" seria conselho de almanaque ocupando o lugar de uma
condição verificável, e ensinaria a pessoa a ignorar a seção inteira.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.analysis.decision import (
    LABELS,
    MOS_BUY,
    MOS_SELL,
    MOS_STRONG_BUY,
    MOS_STRONG_SELL,
)

#: Os limiares, do mais otimista ao mais pessimista. É a mesma lista de
#: `_verdict_from_mos`, lida ao contrário — importada de lá para que mexer em um
#: limiar não deixe a explicação apontando para o antigo.
_BANDS: tuple[tuple[float, str], ...] = (
    (MOS_STRONG_BUY, "STRONG_BUY"),
    (MOS_BUY, "BUY"),
    (MOS_SELL, "HOLD"),
    (MOS_STRONG_SELL, "SELL"),
)

#: Do mais otimista ao mais pessimista, incluindo o degrau final.
_ORDER: tuple[str, ...] = tuple(nome for _, nome in _BANDS) + ("STRONG_SELL",)


@dataclass(frozen=True)
class Falsifier:
    """Uma condição verificável que muda o veredito."""

    metric: str
    #: Frase pronta: o que teria de acontecer.
    condition: str
    #: Para onde o veredito vai se acontecer.
    becomes: str
    becomes_label: str
    #: Onde a métrica está hoje, para a distância ser visível.
    current: float
    #: O valor em que vira.
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
    """Preço que produz exatamente esta margem de segurança.

    ``mos = (justo - preco) / justo`` logo ``preco = justo * (1 - mos)``.
    """
    return consensus * (1 - mos)


def _price_falsifiers(consensus: float, price: float, verdict: str) -> list[Falsifier]:
    """As duas fronteiras vizinhas de preço: a de cima e a de baixo.

    Só as vizinhas. Listar todas as bandas transformaria a seção numa tabela de
    limiares — verdadeira e inútil, porque a pergunta é "o que muda a partir de
    onde estou", não "quais são todos os degraus".
    """
    if verdict not in _ORDER:
        return []

    indice = _ORDER.index(verdict)
    saida: list[Falsifier] = []

    # Para cima: subir de banda exige preço mais baixo (mais desconto).
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

    # Para baixo: descer de banda exige preço mais alto (menos desconto).
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
    """O corte de dividendo que apaga o desconto.

    O consenso é a média dos métodos disponíveis, e só o Bazin depende do
    dividendo. Zerar o desconto significa levar o consenso até o preço atual: o
    Bazin teria de cair para ``n * preco - (soma dos outros metodos)``. Como
    Bazin é proporcional ao dividendo, o corte percentual é o mesmo.

    Devolve ``None`` quando a conta não se sustenta — dividendo que já não
    importa para o consenso, ou desconto que já não existe.
    """
    if not bazin or not consensus or not avg_dividend or consensus_methods < 1:
        return None
    if consensus <= price:
        # Já não há desconto para apagar; a fronteira relevante é o preço.
        return None

    outros = consensus * consensus_methods - bazin
    bazin_alvo = price * consensus_methods - outros
    if bazin_alvo >= bazin:
        # O dividendo teria de **subir** para apagar o desconto: a tese não
        # depende dele nesta direção.
        return None
    if bazin_alvo < 0:
        # Nem suspender o dividendo por inteiro apaga o desconto. Aparar o
        # número em zero produziria a frase "cair 100%" para um corte que na
        # verdade não bastaria — uma conta errada com cara de precisa.
        return None

    corte = 1 - bazin_alvo / bazin
    dividendo_alvo = avg_dividend * bazin_alvo / bazin

    # Um corte de 100% tem nome, e é o nome que a pessoa vai ver no noticiário.
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
    """A inversão de tendência, quando ela participou do veredito.

    O ``decide`` rebaixa compra em tendência de baixa e reforça confiança em
    tendência de alta. Onde a tendência entrou na conta, ela é falsificável;
    onde não entrou, dizer "fique de olho na tendência" seria enfeite.
    """
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
    """As condições que mudam o veredito. Lista vazia é resposta legítima.

    Sem preço ou sem consenso não há régua para ler ao contrário, e inventar uma
    condição plausível seria pior do que não dizer nada: a seção existe
    justamente para ser conferível.
    """
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
