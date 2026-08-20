"""Compensação de prejuízo realizado

`calculate_sell_cost` devolvia IR zero quando havia prejuízo mas não guardava o
saldo negativo para compensar ganhos futuros, como a legislação permite: o app
superestimava o IR devido de qualquer usuário que já tivesse realizado prejuízo.

Revision ID: 0004_tax_loss
Revises: 0003_job_locks
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_tax_loss"
down_revision = "0003_job_locks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("closed_trades", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("loss_offset_used", sa.Float(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column("taxable_profit", sa.Float(), nullable=False, server_default="0")
        )

    # Backfill: vendas antigas não tiveram compensação aplicada, então o lucro
    # tributável é o lucro bruto quando houve IR.
    op.execute(
        "UPDATE closed_trades SET taxable_profit = "
        "CASE WHEN gross_profit > 0 THEN gross_profit ELSE 0 END"
    )


def downgrade() -> None:
    with op.batch_alter_table("closed_trades", schema=None) as batch_op:
        batch_op.drop_column("taxable_profit")
        batch_op.drop_column("loss_offset_used")
