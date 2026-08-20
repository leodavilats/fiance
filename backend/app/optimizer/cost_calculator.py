from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import AssetCategory

IR_ACOES = 0.15
IR_FIIS = 0.20

# Isenção mensal de ganho de capital em ações BR (vendas do mês, não por
# operação isolada).
ISENCAO_MENSAL_ACOES = 20_000.0


@dataclass
class TransactionCost:
    asset_category: str
    gross_profit: float
    ir_amount: float
    ir_rate: float
    net_profit: float
    observation: str = ""
    # Quanto de prejuízo acumulado foi usado para abater o ganho desta venda.
    loss_offset_used: float = 0.0
    # Lucro que efetivamente sofreu tributação, após a compensação.
    taxable_profit: float = 0.0


def calculate_sell_cost(
    asset_category: str,
    quantity: float,
    sell_price: float,
    avg_price: float,
    gross_value_month_before: float = 0.0,
    accumulated_loss: float = 0.0,
) -> TransactionCost:
    """Custo fiscal de uma venda.

    `gross_value_month_before` é o acumulado bruto de vendas já feitas no mês
    nesta categoria — a isenção de R$ 20 mil (ações BR) vale sobre o total do
    mês, não por transação isolada.

    `accumulated_loss` é o saldo de prejuízo realizado disponível na categoria.
    A legislação permite abater prejuízo de ganhos futuros da mesma categoria, e
    o app não guardava esse saldo: **superestimava o IR devido** de qualquer
    usuário que já tivesse realizado prejuízo.
    """
    gross_value = quantity * sell_price
    cost_basis = quantity * avg_price
    gross_profit = gross_value - cost_basis
    gross_value_month_total = gross_value_month_before + gross_value

    if gross_profit <= 0:
        return TransactionCost(
            asset_category=asset_category,
            gross_profit=round(gross_profit, 2),
            ir_amount=0.0,
            ir_rate=0.0,
            net_profit=round(gross_profit, 2),
            observation="Sem lucro — IR não incide. O prejuízo fica disponível "
            "para compensar ganhos futuros da mesma categoria.",
            loss_offset_used=0.0,
            taxable_profit=0.0,
        )

    if asset_category == AssetCategory.acoes_br.value:
        if gross_value_month_total <= ISENCAO_MENSAL_ACOES:
            return TransactionCost(
                asset_category=asset_category,
                gross_profit=round(gross_profit, 2),
                ir_amount=0.0,
                ir_rate=0.0,
                net_profit=round(gross_profit, 2),
                observation=(
                    f"Vendas do mês ≤ R$ {ISENCAO_MENSAL_ACOES:,.0f} → isento de IR "
                    "(ações BR). O prejuízo acumulado fica preservado."
                ),
                loss_offset_used=0.0,
                taxable_profit=0.0,
            )
        ir_rate = IR_ACOES
        base_obs = f"IR {ir_rate * 100:.0f}% sobre ganho de capital."

    elif asset_category == AssetCategory.bdrs.value:
        ir_rate = IR_ACOES
        base_obs = f"IR {ir_rate * 100:.0f}% sobre ganho de capital (BDR), sem isenção mensal."

    elif asset_category == AssetCategory.fiis.value:
        ir_rate = IR_FIIS
        base_obs = f"IR {ir_rate * 100:.0f}% sobre lucro na venda de FII."

    elif asset_category == AssetCategory.etfs.value:
        ir_rate = IR_ACOES
        base_obs = f"IR {ir_rate * 100:.0f}% sobre ganho de capital (ETF), sem isenção mensal."

    else:
        return TransactionCost(
            asset_category=asset_category,
            gross_profit=round(gross_profit, 2),
            ir_amount=0.0,
            ir_rate=0.0,
            net_profit=round(gross_profit, 2),
            observation="IR calculado separadamente para renda fixa.",
        )

    offset = min(max(accumulated_loss, 0.0), gross_profit)
    taxable_profit = gross_profit - offset
    ir_amount = taxable_profit * ir_rate

    observation = base_obs
    if offset > 0:
        observation += (
            f" R$ {offset:,.2f} de prejuízo acumulado abatidos; "
            f"imposto sobre R$ {taxable_profit:,.2f}."
        )

    return TransactionCost(
        asset_category=asset_category,
        gross_profit=round(gross_profit, 2),
        ir_amount=round(ir_amount, 2),
        ir_rate=ir_rate,
        net_profit=round(gross_profit - ir_amount, 2),
        observation=observation,
        loss_offset_used=round(offset, 2),
        taxable_profit=round(taxable_profit, 2),
    )
