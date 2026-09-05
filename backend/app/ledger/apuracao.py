from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal

from app.core.money import ZERO, money, quantize, to_float

from .entries import LedgerEntry, TransactionKind
from .projection import QUANTITY_EPSILON, PositionProjection, _apply, _sequence

ALIQUOTA_ACOES = Decimal("0.15")
ALIQUOTA_FIIS = Decimal("0.20")

_ALIQUOTA_POR_CATEGORIA = {
    "acoes_br": ALIQUOTA_ACOES,
    "bdrs": ALIQUOTA_ACOES,
    "etfs": ALIQUOTA_ACOES,
    "fiis": ALIQUOTA_FIIS,
}

CATEGORIA_PADRAO = "acoes_br"

ISENCAO_MENSAL = Decimal("20000")
CATEGORIA_COM_ISENCAO = "acoes_br"


@dataclass(frozen=True)
class VendaApurada:
    entry_id: int | None
    ticker: str
    categoria: str
    traded_on: str
    quantity: float
    sell_price: float
    avg_price: float
    fees: float
    gross_value: Decimal
    cost_basis: Decimal
    result: Decimal

    @property
    def mes(self) -> str:
        return self.traded_on[:7]

    def as_dict(self) -> dict:
        return {
            "id": self.entry_id,
            "ticker": self.ticker,
            "category": self.categoria,
            "traded_on": self.traded_on,
            "quantity": self.quantity,
            "avg_price": self.avg_price,
            "sell_price": self.sell_price,
            "fees": self.fees,
            "gross_value": to_float(quantize(self.gross_value)),
            "cost_basis": to_float(quantize(self.cost_basis)),
            "gross_profit": to_float(quantize(self.result)),
        }


@dataclass
class ApuracaoMensal:
    mes: str
    categoria: str
    vendas: list[VendaApurada] = field(default_factory=list)

    gross_sales: Decimal = ZERO
    result: Decimal = ZERO

    exempt: bool = False
    loss_offset_used: Decimal = ZERO
    taxable_profit: Decimal = ZERO
    ir_rate: Decimal = ZERO
    ir_amount: Decimal = ZERO

    loss_generated: Decimal = ZERO
    loss_compensable: bool = True

    @property
    def observation(self) -> str:
        if self.exempt and self.result > ZERO:
            return (
                f"Vendas de ações no mês somam R$ {to_float(quantize(self.gross_sales)):,.2f}, "
                f"dentro da isenção de R$ {float(ISENCAO_MENSAL):,.0f} → sem imposto no mês."
            )
        if self.exempt:
            return (
                f"Mês isento (vendas ≤ R$ {float(ISENCAO_MENSAL):,.0f}). Prejuízo apurado em "
                "operação isenta não compensa ganho futuro."
            )
        if self.result < ZERO:
            return (
                f"Prejuízo de R$ {abs(to_float(quantize(self.result))):,.2f} no mês. Fica "
                "disponível para compensar ganho futuro da mesma categoria."
            )
        if self.result == ZERO:
            return "Resultado zero no mês — nada a apurar."

        base = f"IR {to_float(self.ir_rate) * 100:.0f}% sobre o resultado do mês."
        if self.loss_offset_used > ZERO:
            base += (
                f" R$ {to_float(quantize(self.loss_offset_used)):,.2f} de prejuízo acumulado "
                f"abatidos; imposto sobre R$ {to_float(quantize(self.taxable_profit)):,.2f}."
            )
        return base

    def as_dict(self) -> dict:
        return {
            "month": self.mes,
            "category": self.categoria,
            "gross_sales": to_float(quantize(self.gross_sales)),
            "result": to_float(quantize(self.result)),
            "exempt": self.exempt,
            "loss_offset_used": to_float(quantize(self.loss_offset_used)),
            "taxable_profit": to_float(quantize(self.taxable_profit)),
            "ir_rate": to_float(self.ir_rate),
            "ir_amount": to_float(quantize(self.ir_amount)),
            "sales": len(self.vendas),
            "observation": self.observation,
        }


@dataclass
class Apuracao:
    vendas: list[VendaApurada] = field(default_factory=list)
    meses: list[ApuracaoMensal] = field(default_factory=list)
    saldo_de_prejuizo: dict[str, Decimal] = field(default_factory=dict)

    @property
    def ir_total(self) -> Decimal:
        return sum((m.ir_amount for m in self.meses), ZERO)

    @property
    def resultado_total(self) -> Decimal:
        return sum((v.result for v in self.vendas), ZERO)

    def mes(self, mes: str, categoria: str) -> ApuracaoMensal | None:
        for apurado in self.meses:
            if apurado.mes == mes and apurado.categoria == categoria:
                return apurado
        return None

    def ir_da_venda(self, venda: VendaApurada) -> Decimal:
        apurado = self.mes(venda.mes, venda.categoria)
        if apurado is None or apurado.ir_amount <= ZERO:
            return ZERO

        lucros = sum((v.result for v in apurado.vendas if v.result > ZERO), ZERO)
        if lucros <= ZERO or venda.result <= ZERO:
            return ZERO

        return apurado.ir_amount * venda.result / lucros


def _vendas_do_razao(
    entries: Iterable[LedgerEntry],
    categoria_de: dict[str, str] | None = None,
) -> list[VendaApurada]:
    categorias = {k.upper(): v for k, v in (categoria_de or {}).items()}

    por_simbolo: dict[str, list[LedgerEntry]] = {}
    for entry in entries:
        por_simbolo.setdefault(entry.symbol.strip().upper(), []).append(entry)

    vendas: list[VendaApurada] = []

    for simbolo, lancamentos in por_simbolo.items():
        ordenados, _ = _sequence(lancamentos)
        estado = PositionProjection(symbol=simbolo)

        for entry in ordenados:
            if entry.kind is TransactionKind.SELL:
                quantidade = money(entry.quantity)
                if quantidade > estado.quantity_exact + QUANTITY_EPSILON:
                    continue
                media = estado.avg_price_exact
                bruto = quantidade * money(entry.price)
                custo = media * quantidade
                taxas = money(entry.fees)
                vendas.append(
                    VendaApurada(
                        entry_id=entry.id,
                        ticker=simbolo,
                        categoria=categorias.get(simbolo, CATEGORIA_PADRAO),
                        traded_on=entry.traded_on,
                        quantity=float(quantidade),
                        sell_price=entry.price,
                        avg_price=float(media),
                        fees=entry.fees,
                        gross_value=bruto,
                        cost_basis=custo,
                        result=bruto - custo - taxas,
                    )
                )

            _apply(estado, entry)

    vendas.sort(key=lambda v: (v.traded_on, v.entry_id or 0))
    return vendas


def apurar(
    entries: Iterable[LedgerEntry],
    categoria_de: dict[str, str] | None = None,
) -> Apuracao:
    vendas = _vendas_do_razao(entries, categoria_de)

    por_mes: dict[tuple[str, str], ApuracaoMensal] = {}
    for venda in vendas:
        chave = (venda.mes, venda.categoria)
        apurado = por_mes.get(chave)
        if apurado is None:
            apurado = ApuracaoMensal(mes=venda.mes, categoria=venda.categoria)
            por_mes[chave] = apurado
        apurado.vendas.append(venda)
        apurado.gross_sales += venda.gross_value
        apurado.result += venda.result

    saldo: dict[str, Decimal] = {}

    for chave in sorted(por_mes):
        apurado = por_mes[chave]
        categoria = apurado.categoria

        apurado.exempt = (
            categoria == CATEGORIA_COM_ISENCAO and apurado.gross_sales <= ISENCAO_MENSAL
        )

        if apurado.exempt:
            apurado.loss_compensable = False
            if apurado.result < ZERO:
                apurado.loss_generated = ZERO
            continue

        if apurado.result < ZERO:
            apurado.loss_generated = -apurado.result
            saldo[categoria] = saldo.get(categoria, ZERO) + apurado.loss_generated
            continue

        if apurado.result == ZERO:
            continue

        disponivel = saldo.get(categoria, ZERO)
        abatido = min(disponivel, apurado.result)
        apurado.loss_offset_used = abatido
        saldo[categoria] = disponivel - abatido

        apurado.taxable_profit = apurado.result - abatido
        apurado.ir_rate = _ALIQUOTA_POR_CATEGORIA.get(categoria, ALIQUOTA_ACOES)
        apurado.ir_amount = apurado.taxable_profit * apurado.ir_rate

    return Apuracao(
        vendas=vendas,
        meses=[por_mes[chave] for chave in sorted(por_mes)],
        saldo_de_prejuizo={c: s for c, s in saldo.items() if s > ZERO},
    )
