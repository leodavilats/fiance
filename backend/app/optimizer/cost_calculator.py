"""Calculadora de custos de transação por categoria de ativo."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import AssetCategory

# IR sobre ganho de capital
IR_ACOES = 0.15  # 15% para ações (operações normais)
IR_FIIS = 0.20  # 20% sobre rendimentos distribuídos / venda com lucro (abaixo de R$20k/mês isento para ações BR, mas conservadoramente incluímos)
IR_CRIPTO = 0.15  # 15% até R$5M de lucro


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
) -> TransactionCost:
    """
    Calcula os custos de venda de um ativo, incluindo IR sobre ganho de capital.

    Args:
        asset_category: Categoria do ativo (acoes_br, acoes_int, fiis, cripto)
        quantity: Quantidade a vender
        sell_price: Preço de venda por unidade
        avg_price: Preço médio de aquisição por unidade

    Returns:
        TransactionCost com breakdown dos custos
    """
    gross_value = quantity * sell_price
    cost_basis = quantity * avg_price
    gross_profit = gross_value - cost_basis

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
        # Isenção para vendas mensais de ações BR até R$20.000
        if gross_value <= 20_000:
            ir_rate = 0.0
            ir_amount = 0.0
            obs = "Venda ≤ R$20k/mês → isento de IR (ações BR)."
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
        if gross_value <= 35_000:
            ir_rate = 0.0
            ir_amount = 0.0
            obs = "Venda ≤ R$35k/mês → isento de IR (cripto)."
        else:
            ir_rate = IR_CRIPTO
            ir_amount = gross_profit * ir_rate
            obs = f"IR {ir_rate * 100:.0f}% sobre ganho de capital (cripto)."

    else:  # renda_fixa ou desconhecido
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
