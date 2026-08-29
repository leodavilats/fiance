from __future__ import annotations

import sqlalchemy as sa
from alembic import op

import app.core.money

revision = "0002_dinheiro_exato"
down_revision = "0001_esquema_inicial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("closed_trades", schema=None) as batch_op:
        batch_op.alter_column(
            "quantity",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "avg_price",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "sell_price",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "gross_profit",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "ir_amount",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "net_profit",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "loss_offset_used",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "taxable_profit",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )

    with op.batch_alter_table("dividends_received", schema=None) as batch_op:
        batch_op.alter_column(
            "amount",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )

    with op.batch_alter_table("fixed_income_positions", schema=None) as batch_op:
        batch_op.alter_column(
            "valor_investido",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )

    with op.batch_alter_table("followed_suggestions", schema=None) as batch_op:
        batch_op.alter_column(
            "quantity",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "price",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )

    with op.batch_alter_table("goals", schema=None) as batch_op:
        batch_op.alter_column(
            "target_value",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=True,
        )

    with op.batch_alter_table("portfolio", schema=None) as batch_op:
        batch_op.alter_column(
            "quantity",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "avg_price",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )

    with op.batch_alter_table("portfolio_snapshot", schema=None) as batch_op:
        batch_op.alter_column(
            "total_invested",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "total_current",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "total_pnl",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )

    with op.batch_alter_table("preferences", schema=None) as batch_op:
        batch_op.alter_column(
            "cash_available",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "passive_income_goal",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=True,
        )

    with op.batch_alter_table("price_alerts", schema=None) as batch_op:
        batch_op.alter_column(
            "target_price",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )

    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.alter_column(
            "quantity",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "price",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "fees",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "amount",
            existing_type=sa.FLOAT(),
            type_=app.core.money.ExactNumeric(),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.alter_column(
            "amount",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "fees",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "price",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "quantity",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )

    with op.batch_alter_table("price_alerts", schema=None) as batch_op:
        batch_op.alter_column(
            "target_price",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )

    with op.batch_alter_table("preferences", schema=None) as batch_op:
        batch_op.alter_column(
            "passive_income_goal",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "cash_available",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )

    with op.batch_alter_table("portfolio_snapshot", schema=None) as batch_op:
        batch_op.alter_column(
            "total_pnl",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "total_current",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "total_invested",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )

    with op.batch_alter_table("portfolio", schema=None) as batch_op:
        batch_op.alter_column(
            "avg_price",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "quantity",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )

    with op.batch_alter_table("goals", schema=None) as batch_op:
        batch_op.alter_column(
            "target_value",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=True,
        )

    with op.batch_alter_table("followed_suggestions", schema=None) as batch_op:
        batch_op.alter_column(
            "price",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "quantity",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )

    with op.batch_alter_table("fixed_income_positions", schema=None) as batch_op:
        batch_op.alter_column(
            "valor_investido",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )

    with op.batch_alter_table("dividends_received", schema=None) as batch_op:
        batch_op.alter_column(
            "amount",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )

    with op.batch_alter_table("closed_trades", schema=None) as batch_op:
        batch_op.alter_column(
            "taxable_profit",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "loss_offset_used",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "net_profit",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "ir_amount",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "gross_profit",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "sell_price",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "avg_price",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "quantity",
            existing_type=app.core.money.ExactNumeric(),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
