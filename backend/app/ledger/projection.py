from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal

from app.core.money import ZERO, money, quantize

from .entries import LedgerEntry, LedgerError, TransactionKind

QUANTITY_EPSILON = Decimal("0.00000001")


@dataclass
class PositionProjection:
    symbol: str
    quantity_exact: Decimal = ZERO
    total_cost_exact: Decimal = ZERO
    realized_pnl_exact: Decimal = ZERO
    total_fees_exact: Decimal = ZERO
    first_traded_on: str | None = None
    last_traded_on: str | None = None
    entries_applied: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def avg_price_exact(self) -> Decimal:
        if abs(self.quantity_exact) < QUANTITY_EPSILON:
            return ZERO
        return self.total_cost_exact / self.quantity_exact

    @property
    def quantity(self) -> float:
        return float(self.quantity_exact)

    @property
    def total_cost(self) -> float:
        return float(self.total_cost_exact)

    @property
    def realized_pnl(self) -> float:
        return float(self.realized_pnl_exact)

    @property
    def total_fees(self) -> float:
        return float(self.total_fees_exact)

    @property
    def avg_price(self) -> float:
        return float(self.avg_price_exact)

    @property
    def is_open(self) -> bool:
        return self.quantity_exact > QUANTITY_EPSILON

    def as_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "avg_price": self.avg_price,
            "total_cost": float(quantize(self.total_cost_exact)),
            "realized_pnl": float(quantize(self.realized_pnl_exact)),
            "total_fees": float(quantize(self.total_fees_exact)),
            "first_traded_on": self.first_traded_on,
            "last_traded_on": self.last_traded_on,
            "entries_applied": self.entries_applied,
            "warnings": list(self.warnings),
        }


def _apply(state: PositionProjection, entry: LedgerEntry) -> None:
    kind = entry.kind
    quantity = money(entry.quantity)
    price = money(entry.price)
    fees = money(entry.fees)

    if kind is TransactionKind.ADJUST:
        state.quantity_exact = quantity
        state.total_cost_exact = quantity * price
        return

    if kind is TransactionKind.BUY:
        state.quantity_exact += quantity
        state.total_cost_exact += quantity * price + fees
        state.total_fees_exact += fees
        return

    if kind is TransactionKind.SELL:
        if quantity > state.quantity_exact + QUANTITY_EPSILON:
            raise LedgerError(
                f"Venda de {entry.quantity:g} {entry.symbol} em {entry.traded_on} sem posição: "
                f"o razão tem {state.quantity:g}."
            )
        sold_cost = state.avg_price_exact * quantity
        state.realized_pnl_exact += quantity * price - sold_cost - fees
        state.quantity_exact -= quantity
        state.total_cost_exact -= sold_cost
        state.total_fees_exact += fees
        if abs(state.quantity_exact) < QUANTITY_EPSILON:
            state.quantity_exact = ZERO
            state.total_cost_exact = ZERO
        return

    if kind is TransactionKind.SPLIT:
        state.quantity_exact = (
            state.quantity_exact * money(entry.ratio_to) / money(entry.ratio_from)
        )
        return

    if kind is TransactionKind.BONUS:
        state.quantity_exact += quantity
        state.total_cost_exact += quantity * price
        return

    if kind is TransactionKind.AMORTIZATION:
        state.total_cost_exact = max(ZERO, state.total_cost_exact - money(entry.amount))
        return

    if kind is TransactionKind.TRANSFER_IN:
        state.quantity_exact += quantity
        state.total_cost_exact += quantity * price
        return

    if kind is TransactionKind.TRANSFER_OUT:
        if quantity > state.quantity_exact + QUANTITY_EPSILON:
            raise LedgerError(
                f"Transferência de saída de {entry.quantity:g} {entry.symbol} maior que a posição."
            )
        avg = state.avg_price_exact
        state.quantity_exact -= quantity
        state.total_cost_exact -= avg * quantity
        return

    raise LedgerError(f"Tipo de lançamento sem projeção definida: {kind!r}.")


def _sequence(entries: Iterable[LedgerEntry]) -> list[LedgerEntry]:
    por_registro = sorted(entries, key=lambda e: e.id if e.id is not None else 0)

    corte = 0
    for indice, entry in enumerate(por_registro):
        if entry.kind is TransactionKind.ADJUST:
            corte = indice

    relevantes = por_registro[corte:]
    if relevantes and relevantes[0].kind is TransactionKind.ADJUST:
        return [relevantes[0]] + sorted(relevantes[1:], key=lambda e: e.sort_key)
    return sorted(relevantes, key=lambda e: e.sort_key)


def _fold(entries: Iterable[LedgerEntry], symbol: str, on_step=None) -> PositionProjection:
    ordered = _sequence(entries)
    state = PositionProjection(symbol=symbol or (ordered[0].symbol if ordered else ""))

    for entry in ordered:
        _apply(state, entry)
        state.entries_applied += 1
        if state.first_traded_on is None:
            state.first_traded_on = entry.traded_on
        state.last_traded_on = entry.traded_on
        if on_step is not None:
            on_step(entry, state)

    return state


def project_position(entries: Iterable[LedgerEntry], symbol: str = "") -> PositionProjection:
    return _fold(entries, symbol)


def project_positions(entries: Iterable[LedgerEntry]) -> dict[str, PositionProjection]:
    by_symbol: dict[str, list[LedgerEntry]] = {}
    for entry in entries:
        by_symbol.setdefault(entry.symbol.strip().upper(), []).append(entry)

    return {symbol: project_position(rows, symbol) for symbol, rows in by_symbol.items()}


@dataclass
class DerivationStep:
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
    steps: list[DerivationStep] = []

    def record(entry: LedgerEntry, state: PositionProjection) -> None:
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

    state = _fold(entries, symbol, on_step=record)

    return {
        "symbol": state.symbol,
        "position": state.as_dict(),
        "steps": [step.as_dict() for step in steps],
    }
