from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import AssetCategory

IR_ACOES = 0.15
IR_FIIS = 0.20
IR_CRIPTO = 0.15


@dataclass
class TransactionCost:
    asset_category: str
    gross_profit: float
    ir_amount: float
    ir_rate: float
    net_profit: float
    observation: str = ""


def calculate_sell_cost(
    asset_category: str,
    quantity: float,
    sell_price: float,
    avg_price: float,
    gross_value_month_before: float = 0.0,
) -> TransactionCost:
    # gross_value_month_before é o acumulado bruto de vendas já feitas no mês
    # nesta categoria — as isenções (R$20k ações BR, R$35k cripto) valem sobre
    # o total do mês, não por transação isolada.
    gross_value = quantity * sell_price
    cost_basis = quantity * avg_price
    gross_profit = gross_value - cost_basis
    gross_value_month_total = gross_value_month_before + gross_value

    if gross_profit <= 0:
        return TransactionCost(
            asset_category=asset_category,
            gross_profit=gross_profit,
            ir_amount=0.0,
            ir_rate=0.0,
            net_profit=gross_profit,
            observation="Sem lucro — IR não incide.",
        )

    if asset_category == AssetCategory.acoes_br.value:
        if gross_value_month_total <= 20_000:
            ir_rate = 0.0
            ir_amount = 0.0
            obs = "Vendas do mês ≤ R$20k → isento de IR (ações BR)."
        else:
            ir_rate = IR_ACOES
            ir_amount = gross_profit * ir_rate
            obs = f"IR {ir_rate * 100:.0f}% sobre ganho de capital."

    elif asset_category == AssetCategory.acoes_int.value:
        ir_rate = IR_ACOES
        ir_amount = gross_profit * ir_rate
        obs = f"IR {ir_rate * 100:.0f}% sobre ganho de capital (ações internacionais)."

    elif asset_category == AssetCategory.fiis.value:
        ir_rate = IR_FIIS
        ir_amount = gross_profit * ir_rate
        obs = f"IR {ir_rate * 100:.0f}% sobre lucro na venda de FII."

    elif asset_category == AssetCategory.cripto.value:
        if gross_value_month_total <= 35_000:
            ir_rate = 0.0
            ir_amount = 0.0
            obs = "Vendas do mês ≤ R$35k → isento de IR (cripto)."
        else:
            ir_rate = IR_CRIPTO
            ir_amount = gross_profit * ir_rate
            obs = f"IR {ir_rate * 100:.0f}% sobre ganho de capital (cripto)."

    else:
        ir_rate = 0.0
        ir_amount = 0.0
        obs = "IR calculado separadamente para renda fixa."

    return TransactionCost(
        asset_category=asset_category,
        gross_profit=round(gross_profit, 2),
        ir_amount=round(ir_amount, 2),
        ir_rate=ir_rate,
        net_profit=round(gross_profit - ir_amount, 2),
        observation=obs,
    )
