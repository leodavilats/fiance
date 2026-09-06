from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from app.core.money import Money, Quantity

revision = "0006_remove_closed_trades"
down_revision = "0005_sessoes_de_checkout"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("closed_trades")


def downgrade() -> None:
    op.create_table(
        "closed_trades",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.VARCHAR(), nullable=False),
        sa.Column("ticker", sa.VARCHAR(), nullable=False),
        sa.Column("category", sa.VARCHAR(), nullable=False),
        sa.Column("quantity", Quantity(), nullable=False),
        sa.Column("avg_price", Money(), nullable=False),
        sa.Column("sell_price", Money(), nullable=False),
        sa.Column("gross_profit", Money(), nullable=False),
        sa.Column("ir_rate", sa.FLOAT(), nullable=False),
        sa.Column("ir_amount", Money(), nullable=False),
        sa.Column("net_profit", Money(), nullable=False),
        sa.Column("loss_offset_used", Money(), nullable=True),
        sa.Column("taxable_profit", Money(), nullable=True),
        sa.Column("loss_compensable", sa.BOOLEAN(), nullable=False),
        sa.Column("sold_at", sa.FLOAT(), nullable=False),
        sa.Column("created_at", sa.FLOAT(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_closed_trades_user_id"), "closed_trades", ["user_id"], unique=False)
