from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal

from app.core.money import ZERO, money, quantize, sum_money

from .entries import LedgerEntry, LedgerError, TransactionKind

QUANTITY_EPSILON = Decimal("0.00000001")

_PREGAO = frozenset({TransactionKind.BUY, TransactionKind.SELL})


@dataclass(frozen=True)
class Realizacao:
    entry_id: int | None
    traded_on: str
    quantity: Decimal
    sell_value: Decimal
    cost: Decimal
    fees: Decimal
    day_trade: bool = False

    @property
    def result(self) -> Decimal:
        return self.sell_value - self.cost - self.fees

    @property
    def sell_price(self) -> Decimal:
        return self.sell_value / self.quantity

    @property
    def avg_price(self) -> Decimal:
        return self.cost / self.quantity


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
    realizacoes: list[Realizacao] = field(default_factory=list)

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


def _comprar(state: PositionProjection, quantity: Decimal, value: Decimal, fees: Decimal) -> None:
    state.quantity_exact += quantity
    state.total_cost_exact += value + fees
    state.total_fees_exact += fees


def _vender(
    state: PositionProjection,
    quantity: Decimal,
    value: Decimal,
    fees: Decimal,
    entry_id: int | None,
    traded_on: str,
) -> None:
    sold_cost = state.avg_price_exact * quantity
    realizacao = Realizacao(entry_id, traded_on, quantity, value, sold_cost, fees)
    state.realizacoes.append(realizacao)
    state.realized_pnl_exact += realizacao.result
    state.quantity_exact -= quantity
    state.total_cost_exact -= sold_cost
    state.total_fees_exact += fees
    if abs(state.quantity_exact) < QUANTITY_EPSILON:
        state.quantity_exact = ZERO
        state.total_cost_exact = ZERO


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
        _comprar(state, quantity, quantity * price, fees)
        return

    if kind is TransactionKind.SELL:
        if quantity > state.quantity_exact + QUANTITY_EPSILON:
            raise LedgerError(
                f"Venda de {entry.quantity:g} {entry.symbol} em {entry.traded_on} sem posição: "
                f"o razão tem {state.quantity:g}."
            )
        _vender(state, quantity, quantity * price, fees, entry.id, entry.traded_on)
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
        amortizado = money(entry.amount)
        excedente = amortizado - state.total_cost_exact
        state.total_cost_exact = max(ZERO, state.total_cost_exact - amortizado)
        if excedente > ZERO:
            state.warnings.append(
                f"Amortização de {entry.traded_on} excedeu o custo restante em "
                f"R$ {float(excedente):.2f}. Esse excedente é ganho tributável e não "
                f"está apurado aqui."
            )
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


_KINDS_QUE_SOMAM = frozenset(
    {TransactionKind.BUY, TransactionKind.BONUS, TransactionKind.TRANSFER_IN}
)


def _sequence(entries: Iterable[LedgerEntry]) -> tuple[list[LedgerEntry], list[LedgerEntry]]:
    por_registro = sorted(entries, key=lambda e: e.id if e.id is not None else 0)

    corte = 0
    for indice, entry in enumerate(por_registro):
        if entry.kind is TransactionKind.ADJUST:
            corte = indice

    relevantes = por_registro[corte:]
    if not relevantes or relevantes[0].kind is not TransactionKind.ADJUST:
        return sorted(relevantes, key=lambda e: e.sort_key), []

    ancora = relevantes[0]

    aplicaveis: list[LedgerEntry] = []
    absorvidos: list[LedgerEntry] = []
    for entry in relevantes[1:]:
        if entry.traded_on < ancora.traded_on and entry.kind in _KINDS_QUE_SOMAM:
            absorvidos.append(entry)
        else:
            aplicaveis.append(entry)

    return [ancora] + sorted(aplicaveis, key=lambda e: e.sort_key), absorvidos


def _pregoes_com_day_trade(ordered: list[LedgerEntry]) -> dict[str, list[LedgerEntry]]:
    por_dia: dict[str, list[LedgerEntry]] = {}
    for entry in ordered:
        if entry.kind in _PREGAO:
            por_dia.setdefault(entry.traded_on, []).append(entry)
    return {dia: bloco for dia, bloco in por_dia.items() if {e.kind for e in bloco} == _PREGAO}


def _apply_day_trade(
    state: PositionProjection, bloco: list[LedgerEntry], tolerant: bool
) -> Realizacao:
    compras = [e for e in bloco if e.kind is TransactionKind.BUY]
    vendas = [e for e in bloco if e.kind is TransactionKind.SELL]
    dia = bloco[0].traded_on
    venda_id = max((e.id for e in vendas if e.id is not None), default=None)

    comprado = sum_money(e.quantity for e in compras)
    valor_compras = sum_money(money(e.quantity) * money(e.price) for e in compras)
    taxas_compras = sum_money(e.fees for e in compras)
    vendido = sum_money(e.quantity for e in vendas)
    valor_vendas = sum_money(money(e.quantity) * money(e.price) for e in vendas)
    taxas_vendas = sum_money(e.fees for e in vendas)

    casado = min(comprado, vendido)
    custo_casado = casado * valor_compras / comprado
    venda_casada = casado * valor_vendas / vendido
    taxas_compra_casada = taxas_compras * casado / comprado
    taxas_venda_casada = taxas_vendas * casado / vendido

    day_trade = Realizacao(
        entry_id=venda_id,
        traded_on=dia,
        quantity=casado,
        sell_value=venda_casada,
        cost=custo_casado,
        fees=taxas_compra_casada + taxas_venda_casada,
        day_trade=True,
    )
    state.realizacoes.append(day_trade)
    state.realized_pnl_exact += day_trade.result
    state.total_fees_exact += day_trade.fees

    sobra_compra = comprado - casado
    sobra_venda = vendido - casado
    if sobra_compra > QUANTITY_EPSILON:
        _comprar(
            state,
            sobra_compra,
            valor_compras - custo_casado,
            taxas_compras - taxas_compra_casada,
        )
    elif sobra_venda > QUANTITY_EPSILON:
        if sobra_venda <= state.quantity_exact + QUANTITY_EPSILON:
            _vender(
                state,
                sobra_venda,
                valor_vendas - venda_casada,
                taxas_vendas - taxas_venda_casada,
                venda_id,
                dia,
            )
        elif not tolerant:
            raise LedgerError(
                f"Venda de {float(sobra_venda):g} {bloco[0].symbol} em {dia} sem posição: "
                f"o day trade do dia casou {float(casado):g}, e o razão tem {state.quantity:g}."
            )

    return day_trade


def _venda_sem_posicao(state: PositionProjection, entry: LedgerEntry) -> bool:
    return (
        entry.kind is TransactionKind.SELL
        and money(entry.quantity) > state.quantity_exact + QUANTITY_EPSILON
    )


def _fold(
    entries: Iterable[LedgerEntry],
    symbol: str,
    on_step=None,
    tolerant: bool = False,
) -> PositionProjection:
    ordered, ignorados = _sequence(entries)
    state = PositionProjection(symbol=symbol or (ordered[0].symbol if ordered else ""))

    if ignorados:
        ancora = ordered[0].traded_on if ordered else "?"
        state.warnings.append(
            f"{len(ignorados)} lançamento(s) de entrada anteriores à declaração de posição "
            f"de {ancora} não foram somados: o que foi declarado já os contém."
        )

    pregoes = _pregoes_com_day_trade(ordered)

    for entry in ordered:
        bloco = pregoes.get(entry.traded_on) if entry.kind in _PREGAO else None
        day_trade = None
        if bloco is not None:
            if entry is not bloco[0]:
                continue
            day_trade = _apply_day_trade(state, bloco, tolerant)
            state.entries_applied += len(bloco)
        elif tolerant and _venda_sem_posicao(state, entry):
            continue
        else:
            _apply(state, entry)
            state.entries_applied += 1
        if state.first_traded_on is None:
            state.first_traded_on = entry.traded_on
        state.last_traded_on = entry.traded_on
        if on_step is not None:
            on_step(entry, state, day_trade)

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


def _describe_day_trade(day_trade: Realizacao, state: PositionProjection) -> str:
    return (
        f"Day trade de {float(day_trade.quantity):g}: compra média "
        f"{float(day_trade.avg_price):.2f}, venda média {float(day_trade.sell_price):.2f}, "
        f"resultado {float(quantize(day_trade.result)):.2f} apurado à parte. "
        f"O que sobrou do dia entra na média, que fica em {state.avg_price:.4f}."
    )


def explain_position(entries: Iterable[LedgerEntry], symbol: str = "") -> dict:
    steps: list[DerivationStep] = []

    def record(entry: LedgerEntry, state: PositionProjection, day_trade: Realizacao | None) -> None:
        steps.append(
            DerivationStep(
                traded_on=entry.traded_on,
                kind="day_trade" if day_trade else entry.kind.value,
                description=(
                    _describe_day_trade(day_trade, state) if day_trade else _describe(entry, state)
                ),
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
