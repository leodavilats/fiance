"""Proventos recebidos

Todo número de renda no produto era estimativa derivada de DY
(`monthly_dividends_estimate`) e o histórico real não era armazenado em tabela
nenhuma: "quanto eu recebi este mês" não tinha resposta.

Revision ID: 0005_dividends
Revises: 0004_tax_loss
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_dividends"
down_revision = "0004_tax_loss"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dividends_received",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("paid_at", sa.String(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("dividends_received", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_dividends_received_user_id"), ["user_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_dividends_received_ticker"), ["ticker"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_dividends_received_paid_at"), ["paid_at"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("dividends_received", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_dividends_received_paid_at"))
        batch_op.drop_index(batch_op.f("ix_dividends_received_ticker"))
        batch_op.drop_index(batch_op.f("ix_dividends_received_user_id"))
    op.drop_table("dividends_received")
