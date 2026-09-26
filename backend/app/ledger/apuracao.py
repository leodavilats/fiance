from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal

from app.core.money import ZERO, quantize, to_float

from .entries import LedgerEntry
from .projection import _fold

ALIQUOTA_ACOES = Decimal("0.15")
ALIQUOTA_FIIS = Decimal("0.20")
ALIQUOTA_DAY_TRADE = Decimal("0.20")
IRRF_DAY_TRADE = Decimal("0.01")

_ALIQUOTA_POR_CATEGORIA = {
    "acoes_br": ALIQUOTA_ACOES,
    "bdrs": ALIQUOTA_ACOES,
    "etfs": ALIQUOTA_ACOES,
    "fiis": ALIQUOTA_FIIS,
}

CATEGORIA_PADRAO = "acoes_br"

ISENCAO_MENSAL = Decimal("20000")
CATEGORIA_COM_ISENCAO = "acoes_br"


def _reais(valor: Decimal) -> str:
    return f"R$ {to_float(quantize(valor)):,.2f}"


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
    day_trade: bool = False

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
            "day_trade": self.day_trade,
        }


@dataclass
class ApuracaoMensal:
    mes: str
    categoria: str
    day_trade: bool = False
    vendas: list[VendaApurada] = field(default_factory=list)

    gross_sales: Decimal = ZERO
    exemption_sales: Decimal = ZERO
    result: Decimal = ZERO

    exempt: bool = False
    loss_offset_used: Decimal = ZERO
    taxable_profit: Decimal = ZERO
    ir_rate: Decimal = ZERO
    ir_amount: Decimal = ZERO

    irrf_withheld: Decimal = ZERO
    irrf_deducted: Decimal = ZERO

    loss_generated: Decimal = ZERO
    loss_compensable: bool = True

    @property
    def ir_payable(self) -> Decimal:
        return self.ir_amount - self.irrf_deducted

    @property
    def observation(self) -> str:
        if self.day_trade:
            return self._observacao_day_trade()

        com_day_trade = self.exemption_sales > self.gross_sales
        if self.exempt and self.result > ZERO:
            origem = ", com as de day trade," if com_day_trade else ""
            return (
                f"Vendas de ações no mês{origem} somam {_reais(self.exemption_sales)}, "
                f"dentro da isenção de R$ {float(ISENCAO_MENSAL):,.0f} → sem imposto no mês."
            )
        if self.exempt:
            return (
                f"Mês isento (vendas ≤ R$ {float(ISENCAO_MENSAL):,.0f}). Prejuízo apurado em "
                "operação isenta não compensa ganho futuro."
            )

        base = self._observacao_tributavel()
        if (
            self.categoria == CATEGORIA_COM_ISENCAO
            and self.gross_sales <= ISENCAO_MENSAL < self.exemption_sales
        ):
            base += (
                f" As vendas de day trade levam o volume do mês a {_reais(self.exemption_sales)}, "
                "acima da isenção."
            )
        return base

    def _observacao_tributavel(self) -> str:
        if self.result < ZERO:
            return (
                f"Prejuízo de {_reais(-self.result)} no mês. Fica "
                "disponível para compensar ganho futuro da mesma categoria."
            )
        if self.result == ZERO:
            return "Resultado zero no mês — nada a apurar."

        base = f"IR {to_float(self.ir_rate) * 100:.0f}% sobre o resultado do mês."
        if self.loss_offset_used > ZERO:
            base += (
                f" {_reais(self.loss_offset_used)} de prejuízo acumulado "
                f"abatidos; imposto sobre {_reais(self.taxable_profit)}."
            )
        return base

    def _observacao_day_trade(self) -> str:
        if self.result < ZERO:
            texto = (
                f"Prejuízo de day trade de {_reais(-self.result)} no mês. Compensa só ganho "
                "de day trade da mesma categoria."
            )
        elif self.result == ZERO:
            texto = "Resultado zero de day trade no mês — nada a apurar."
        else:
            texto = "Day trade: IR 20% sobre o resultado do mês, sem isenção."
            if self.loss_offset_used > ZERO:
                texto += (
                    f" {_reais(self.loss_offset_used)} de prejuízo de day trade abatidos; "
                    f"imposto sobre {_reais(self.taxable_profit)}."
                )

        if self.irrf_deducted > ZERO:
            texto += (
                f" {_reais(self.irrf_deducted)} de IRRF (1% que a corretora retém) deduzidos; "
                f"a pagar {_reais(self.ir_payable)}."
            )
        elif self.irrf_withheld > ZERO:
            texto += (
                f" {_reais(self.irrf_withheld)} retidos na fonte ficam para deduzir de imposto "
                "de day trade futuro."
            )
        return texto

    def as_dict(self) -> dict:
        return {
            "month": self.mes,
            "category": self.categoria,
            "day_trade": self.day_trade,
            "gross_sales": to_float(quantize(self.gross_sales)),
            "result": to_float(quantize(self.result)),
            "exempt": self.exempt,
            "loss_offset_used": to_float(quantize(self.loss_offset_used)),
            "taxable_profit": to_float(quantize(self.taxable_profit)),
            "ir_rate": to_float(self.ir_rate),
            "ir_amount": to_float(quantize(self.ir_amount)),
            "irrf_withheld": to_float(quantize(self.irrf_withheld)),
            "irrf_deducted": to_float(quantize(self.irrf_deducted)),
            "ir_payable": to_float(quantize(self.ir_payable)),
            "sales": len(self.vendas),
            "observation": self.observation,
        }


@dataclass
class Apuracao:
    vendas: list[VendaApurada] = field(default_factory=list)
    meses: list[ApuracaoMensal] = field(default_factory=list)
    saldo_de_prejuizo: dict[str, Decimal] = field(default_factory=dict)
    saldo_de_prejuizo_day_trade: dict[str, Decimal] = field(default_factory=dict)
    saldo_de_irrf: dict[str, Decimal] = field(default_factory=dict)

    @property
    def ir_total(self) -> Decimal:
        return sum((m.ir_amount for m in self.meses), ZERO)

    @property
    def resultado_total(self) -> Decimal:
        return sum((v.result for v in self.vendas), ZERO)

    def mes(self, mes: str, categoria: str, day_trade: bool = False) -> ApuracaoMensal | None:
        for apurado in self.meses:
            if apurado.mes == mes and apurado.categoria == categoria:
                if apurado.day_trade is day_trade:
                    return apurado
        return None

    def ir_da_venda(self, venda: VendaApurada) -> Decimal:
        apurado = self.mes(venda.mes, venda.categoria, venda.day_trade)
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
        categoria = categorias.get(simbolo, CATEGORIA_PADRAO)
        estado = _fold(lancamentos, simbolo, tolerant=True)
        for realizacao in estado.realizacoes:
            vendas.append(
                VendaApurada(
                    entry_id=realizacao.entry_id,
                    ticker=simbolo,
                    categoria=categoria,
                    traded_on=realizacao.traded_on,
                    quantity=float(realizacao.quantity),
                    sell_price=float(realizacao.sell_price),
                    avg_price=float(realizacao.avg_price),
                    fees=float(realizacao.fees),
                    gross_value=realizacao.sell_value,
                    cost_basis=realizacao.cost,
                    result=realizacao.result,
                    day_trade=realizacao.day_trade,
                )
            )

    vendas.sort(key=lambda v: (v.traded_on, v.entry_id or 0, v.day_trade))
    return vendas


def _irrf_por_mes(vendas: list[VendaApurada]) -> dict[tuple[str, str], Decimal]:
    resultado_do_dia: dict[tuple[str, str], Decimal] = {}
    for venda in vendas:
        if venda.day_trade:
            chave = (venda.traded_on, venda.categoria)
            resultado_do_dia[chave] = resultado_do_dia.get(chave, ZERO) + venda.result

    retido: dict[tuple[str, str], Decimal] = {}
    for (dia, categoria), resultado in resultado_do_dia.items():
        if resultado > ZERO:
            chave = (dia[:7], categoria)
            retido[chave] = retido.get(chave, ZERO) + resultado * IRRF_DAY_TRADE
    return retido


def _tributar(apurado: ApuracaoMensal, saldo: dict[tuple[str, bool], Decimal]) -> None:
    conta = (apurado.categoria, apurado.day_trade)

    apurado.exempt = (
        not apurado.day_trade
        and apurado.categoria == CATEGORIA_COM_ISENCAO
        and apurado.exemption_sales <= ISENCAO_MENSAL
    )

    if apurado.exempt:
        apurado.loss_compensable = False
        return

    if apurado.result < ZERO:
        apurado.loss_generated = -apurado.result
        saldo[conta] = saldo.get(conta, ZERO) + apurado.loss_generated
        return

    if apurado.result == ZERO:
        return

    disponivel = saldo.get(conta, ZERO)
    abatido = min(disponivel, apurado.result)
    apurado.loss_offset_used = abatido
    saldo[conta] = disponivel - abatido

    apurado.taxable_profit = apurado.result - abatido
    if apurado.day_trade:
        apurado.ir_rate = ALIQUOTA_DAY_TRADE
    else:
        apurado.ir_rate = _ALIQUOTA_POR_CATEGORIA.get(apurado.categoria, ALIQUOTA_ACOES)
    apurado.ir_amount = apurado.taxable_profit * apurado.ir_rate


def apurar(
    entries: Iterable[LedgerEntry],
    categoria_de: dict[str, str] | None = None,
) -> Apuracao:
    vendas = _vendas_do_razao(entries, categoria_de)

    por_mes: dict[tuple[str, str, bool], ApuracaoMensal] = {}
    for venda in vendas:
        chave = (venda.mes, venda.categoria, venda.day_trade)
        apurado = por_mes.get(chave)
        if apurado is None:
            apurado = ApuracaoMensal(
                mes=venda.mes, categoria=venda.categoria, day_trade=venda.day_trade
            )
            por_mes[chave] = apurado
        apurado.vendas.append(venda)
        apurado.gross_sales += venda.gross_value
        apurado.result += venda.result

    for (mes, categoria, day_trade), apurado in por_mes.items():
        apurado.exemption_sales = apurado.gross_sales
        if not day_trade and (mes, categoria, True) in por_mes:
            apurado.exemption_sales += por_mes[(mes, categoria, True)].gross_sales

    for (mes, categoria), retido in _irrf_por_mes(vendas).items():
        por_mes[(mes, categoria, True)].irrf_withheld = retido

    saldo: dict[tuple[str, bool], Decimal] = {}
    saldo_de_irrf: dict[str, Decimal] = {}

    for chave in sorted(por_mes):
        apurado = por_mes[chave]
        _tributar(apurado, saldo)

        if apurado.day_trade:
            credito = saldo_de_irrf.get(apurado.categoria, ZERO) + apurado.irrf_withheld
            apurado.irrf_deducted = min(credito, apurado.ir_amount)
            saldo_de_irrf[apurado.categoria] = credito - apurado.irrf_deducted

    return Apuracao(
        vendas=vendas,
        meses=[por_mes[chave] for chave in sorted(por_mes)],
        saldo_de_prejuizo={c: s for (c, dt), s in saldo.items() if not dt and s > ZERO},
        saldo_de_prejuizo_day_trade={c: s for (c, dt), s in saldo.items() if dt and s > ZERO},
        saldo_de_irrf={c: s for c, s in saldo_de_irrf.items() if s > ZERO},
    )
