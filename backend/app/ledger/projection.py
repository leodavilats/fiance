"""A posição corrente como resultado dos lançamentos, e não como estado solto.

O preço médio segue a convenção brasileira, que é a que a Receita usa: venda
não altera o preço médio, apenas reduz quantidade e custo proporcionalmente.
O lucro da venda sai da diferença contra esse preço médio — e é por isso que um
desdobramento não ajustado vira IR errado.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from .entries import LedgerEntry, LedgerError, TransactionKind

#: Abaixo disto a posição é considerada zerada. Existe porque quantidade
#: fracionária vinda de desdobramento acumula resíduo de ponto flutuante — e a
#: troca por Decimal é um refactor à parte, deliberadamente separado deste.
QUANTITY_EPSILON = 1e-9


@dataclass
class PositionProjection:
    symbol: str
    quantity: float = 0.0
    #: Custo total da posição em aberto. O preço médio é derivado dele, nunca
    #: guardado — guardar os dois é criar duas fontes de verdade que divergem.
    total_cost: float = 0.0
    realized_pnl: float = 0.0
    total_fees: float = 0.0
    first_traded_on: str | None = None
    last_traded_on: str | None = None
    entries_applied: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def avg_price(self) -> float:
        if abs(self.quantity) < QUANTITY_EPSILON:
            return 0.0
        return self.total_cost / self.quantity

    @property
    def is_open(self) -> bool:
        return self.quantity > QUANTITY_EPSILON

    def as_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "avg_price": self.avg_price,
            "total_cost": self.total_cost,
            "realized_pnl": self.realized_pnl,
            "total_fees": self.total_fees,
            "first_traded_on": self.first_traded_on,
            "last_traded_on": self.last_traded_on,
            "entries_applied": self.entries_applied,
            "warnings": list(self.warnings),
        }


def _apply(state: PositionProjection, entry: LedgerEntry) -> None:
    kind = entry.kind

    if kind is TransactionKind.ADJUST:
        # Estado declarado: substitui, não soma. As taxas já pagas continuam
        # somadas porque são fato histórico, não parte da posição.
        state.quantity = entry.quantity
        state.total_cost = entry.quantity * entry.price
        return

    if kind is TransactionKind.BUY:
        # Corretagem entra no custo de aquisição — é assim que a Receita
        # calcula o preço médio, e ignorá-la infla o lucro tributável.
        state.quantity += entry.quantity
        state.total_cost += entry.quantity * entry.price + entry.fees
        state.total_fees += entry.fees
        return

    if kind is TransactionKind.SELL:
        if entry.quantity > state.quantity + QUANTITY_EPSILON:
            raise LedgerError(
                f"Venda de {entry.quantity:g} {entry.symbol} em {entry.traded_on} sem posição: "
                f"o razão tem {state.quantity:g}."
            )
        avg = state.avg_price
        sold_cost = avg * entry.quantity
        state.realized_pnl += entry.quantity * entry.price - sold_cost - entry.fees
        state.quantity -= entry.quantity
        state.total_cost -= sold_cost
        state.total_fees += entry.fees
        if abs(state.quantity) < QUANTITY_EPSILON:
            state.quantity = 0.0
            state.total_cost = 0.0
        return

    if kind is TransactionKind.SPLIT:
        # Custo total intacto de propósito: desdobrar não custa nem rende nada.
        # A quantidade muda, e o preço médio cai (ou sobe, no grupamento) na
        # mesma proporção — que é exatamente o ajuste que a Receita espera.
        factor = entry.ratio_to / entry.ratio_from
        state.quantity *= factor
        return

    if kind is TransactionKind.BONUS:
        state.quantity += entry.quantity
        state.total_cost += entry.quantity * entry.price
        return

    if kind is TransactionKind.AMORTIZATION:
        # Devolução de capital: reduz o custo, não a quantidade. Custo não
        # desce de zero — o excedente já é rendimento, não devolução.
        state.total_cost = max(0.0, state.total_cost - entry.amount)
        return

    if kind is TransactionKind.TRANSFER_IN:
        state.quantity += entry.quantity
        state.total_cost += entry.quantity * entry.price
        return

    if kind is TransactionKind.TRANSFER_OUT:
        if entry.quantity > state.quantity + QUANTITY_EPSILON:
            raise LedgerError(
                f"Transferência de saída de {entry.quantity:g} {entry.symbol} maior que a posição."
            )
        avg = state.avg_price
        state.quantity -= entry.quantity
        state.total_cost -= avg * entry.quantity
        return

    raise LedgerError(f"Tipo de lançamento sem projeção definida: {kind!r}.")


def project_position(entries: Iterable[LedgerEntry], symbol: str = "") -> PositionProjection:
    """Dobra os lançamentos de um ativo na posição que eles produzem."""
    ordered = sorted(entries, key=lambda e: e.sort_key)
    state = PositionProjection(symbol=symbol or (ordered[0].symbol if ordered else ""))

    for entry in ordered:
        _apply(state, entry)
        state.entries_applied += 1
        if state.first_traded_on is None:
            state.first_traded_on = entry.traded_on
        state.last_traded_on = entry.traded_on

    return state


def project_positions(entries: Iterable[LedgerEntry]) -> dict[str, PositionProjection]:
    """Projeta a carteira inteira, um ativo por vez.

    Devolve todos os ativos, inclusive os zerados: uma posição encerrada ainda
    carrega lucro realizado, e é isso que a apuração de IR consome.
    """
    by_symbol: dict[str, list[LedgerEntry]] = {}
    for entry in entries:
        by_symbol.setdefault(entry.symbol.strip().upper(), []).append(entry)

    return {symbol: project_position(rows, symbol) for symbol, rows in by_symbol.items()}


@dataclass
class DerivationStep:
    """Um passo da conta, em número e em frase."""

    traded_on: str
    kind: str
    description: str
    quantity_after: float
    total_cost_after: float
    avg_price_after: float

    def as_dict(self) -> dict:
        return {
            "traded_on": self.traded_on,
            "kind": self.kind,
            "description": self.description,
            "quantity_after": round(self.quantity_after, 8),
            "total_cost_after": round(self.total_cost_after, 4),
            "avg_price_after": round(self.avg_price_after, 6),
        }


def _describe(entry: LedgerEntry, state: PositionProjection) -> str:
    kind = entry.kind

    if kind is TransactionKind.BUY:
        fee = f" + {entry.fees:.2f} de custo" if entry.fees else ""
        return (
            f"Compra de {entry.quantity:g} a {entry.price:.2f}{fee}: "
            f"custo sobe para {state.total_cost:.2f}."
        )
    if kind is TransactionKind.SELL:
        return (
            f"Venda de {entry.quantity:g} a {entry.price:.2f}: sai do custo "
            f"{entry.quantity:g} × {state.avg_price:.4f} — a média não muda."
        )
    if kind is TransactionKind.SPLIT:
        verb = "Desdobramento" if entry.ratio_to > entry.ratio_from else "Grupamento"
        return (
            f"{verb} {entry.ratio_from:g}:{entry.ratio_to:g}: quantidade × "
            f"{entry.ratio_to / entry.ratio_from:g}, custo total intacto — "
            f"a média cai para {state.avg_price:.4f}."
        )
    if kind is TransactionKind.BONUS:
        return f"Bonificação de {entry.quantity:g} ao custo declarado de {entry.price:.2f}."
    if kind is TransactionKind.AMORTIZATION:
        return f"Amortização de {entry.amount:.2f}: devolve capital, reduz o custo."
    if kind is TransactionKind.TRANSFER_IN:
        return f"Transferência de entrada de {entry.quantity:g} a {entry.price:.2f}."
    if kind is TransactionKind.TRANSFER_OUT:
        return f"Transferência de saída de {entry.quantity:g}: sai pelo preço médio."
    return (
        f"Estado declarado: {entry.quantity:g} a {entry.price:.2f}. "
        "Substitui o acumulado em vez de somar."
    )


def explain_position(entries: Iterable[LedgerEntry], symbol: str = "") -> dict:
    """A conta do preço médio, passo a passo, em número e em frase.

    Preço médio que ninguém consegue conferir é preço médio em que ninguém
    confia — e é o número que vai para a declaração de IR.
    """
    ordered = sorted(entries, key=lambda e: e.sort_key)
    state = PositionProjection(symbol=symbol or (ordered[0].symbol if ordered else ""))
    steps: list[DerivationStep] = []

    for entry in ordered:
        _apply(state, entry)
        state.entries_applied += 1
        if state.first_traded_on is None:
            state.first_traded_on = entry.traded_on
        state.last_traded_on = entry.traded_on

        steps.append(
            DerivationStep(
                traded_on=entry.traded_on,
                kind=entry.kind.value,
                description=_describe(entry, state),
                quantity_after=state.quantity,
                total_cost_after=state.total_cost,
                avg_price_after=state.avg_price,
            )
        )

    return {
        "symbol": state.symbol,
        "position": state.as_dict(),
        "steps": [step.as_dict() for step in steps],
    }
