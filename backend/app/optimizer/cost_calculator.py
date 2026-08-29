from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.core.money import ZERO, money, quantize, to_float
from app.models.enums import AssetCategory

IR_ACOES = 0.15
IR_FIIS = 0.20

_IR_ACOES = Decimal("0.15")
_IR_FIIS = Decimal("0.20")

ISENCAO_MENSAL_ACOES = 20_000.0
_ISENCAO_MENSAL_ACOES = Decimal("20000")


@dataclass
class TransactionCost:
    asset_category: str
    gross_profit: float
    ir_amount: float
    ir_rate: float
    net_profit: float
    observation: str = ""
    loss_offset_used: float = 0.0
    taxable_profit: float = 0.0
    loss_compensable: bool = True


def calculate_sell_cost(
    asset_category: str,
    quantity: float,
    sell_price: float,
    avg_price: float,
    gross_value_month_before: float = 0.0,
    accumulated_loss: float = 0.0,
) -> TransactionCost:
    gross_value = money(quantity) * money(sell_price)
    cost_basis = money(quantity) * money(avg_price)
    gross_profit = gross_value - cost_basis
    gross_value_month_total = money(gross_value_month_before) + gross_value

    exempt_month = (
        asset_category == AssetCategory.acoes_br.value
        and gross_value_month_total <= _ISENCAO_MENSAL_ACOES
    )

    if gross_profit <= ZERO:
        if exempt_month:
            observation = (
                f"Sem lucro e vendas do mês ≤ R$ {ISENCAO_MENSAL_ACOES:,.0f} → operação "
                "isenta. Prejuízo apurado em operação isenta **não** pode compensar "
                "ganhos futuros."
            )
        else:
            observation = (
                "Sem lucro — IR não incide. O prejuízo fica disponível "
                "para compensar ganhos futuros da mesma categoria."
            )
        return TransactionCost(
            asset_category=asset_category,
            gross_profit=to_float(quantize(gross_profit)),
            ir_amount=0.0,
            ir_rate=0.0,
            net_profit=to_float(quantize(gross_profit)),
            observation=observation,
            loss_offset_used=0.0,
            taxable_profit=0.0,
            loss_compensable=not exempt_month,
        )

    if asset_category == AssetCategory.acoes_br.value:
        if exempt_month:
            return TransactionCost(
                asset_category=asset_category,
                gross_profit=to_float(quantize(gross_profit)),
                ir_amount=0.0,
                ir_rate=0.0,
                net_profit=to_float(quantize(gross_profit)),
                observation=(
                    f"Vendas do mês ≤ R$ {ISENCAO_MENSAL_ACOES:,.0f} → isento de IR "
                    "(ações BR). O prejuízo acumulado fica preservado."
                ),
                loss_offset_used=0.0,
                taxable_profit=0.0,
            )
        rate = _IR_ACOES
        base_obs = f"IR {rate * 100:.0f}% sobre ganho de capital."

    elif asset_category == AssetCategory.bdrs.value:
        rate = _IR_ACOES
        base_obs = f"IR {rate * 100:.0f}% sobre ganho de capital (BDR), sem isenção mensal."

    elif asset_category == AssetCategory.fiis.value:
        rate = _IR_FIIS
        base_obs = f"IR {rate * 100:.0f}% sobre lucro na venda de FII."

    elif asset_category == AssetCategory.etfs.value:
        rate = _IR_ACOES
        base_obs = f"IR {rate * 100:.0f}% sobre ganho de capital (ETF), sem isenção mensal."

    else:
        return TransactionCost(
            asset_category=asset_category,
            gross_profit=to_float(quantize(gross_profit)),
            ir_amount=0.0,
            ir_rate=0.0,
            net_profit=to_float(quantize(gross_profit)),
            observation="IR calculado separadamente para renda fixa.",
        )

    offset = min(max(money(accumulated_loss), ZERO), gross_profit)
    taxable_profit = gross_profit - offset
    ir_amount = taxable_profit * rate

    observation = base_obs
    if offset > ZERO:
        observation += (
            f" R$ {offset:,.2f} de prejuízo acumulado abatidos; "
            f"imposto sobre R$ {taxable_profit:,.2f}."
        )

    return TransactionCost(
        asset_category=asset_category,
        gross_profit=to_float(quantize(gross_profit)),
        ir_amount=to_float(quantize(ir_amount)),
        ir_rate=float(rate),
        net_profit=to_float(quantize(gross_profit - ir_amount)),
        observation=observation,
        loss_offset_used=to_float(quantize(offset)),
        taxable_profit=to_float(quantize(taxable_profit)),
    )
