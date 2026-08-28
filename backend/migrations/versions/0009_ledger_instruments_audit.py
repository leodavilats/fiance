"""Livro-razao: transacoes, instrumentos e log de auditoria (G1)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009_ledger_instruments_audit"
down_revision = "0008_session_usage_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "instruments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("asset_type", sa.String(), nullable=False, server_default="br_stock"),
        sa.Column("name", sa.String(), nullable=False, server_default=""),
        sa.Column("isin", sa.String(), nullable=True),
        sa.Column("valid_from", sa.String(), nullable=False, server_default="1900-01-01"),
        sa.Column("valid_to", sa.String(), nullable=True),
        sa.Column("created_at", sa.Float(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_instruments_symbol", "instruments", ["symbol"])

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=True),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("price", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("fees", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("ratio_from", sa.Float(), nullable=False, server_default=sa.text("1")),
        sa.Column("ratio_to", sa.Float(), nullable=False, server_default=sa.text("1")),
        sa.Column("amount", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("traded_on", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False, server_default="manual"),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("created_at", sa.Float(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])
    op.create_index("ix_transactions_instrument_id", "transactions", ["instrument_id"])
    op.create_index("ix_transactions_symbol", "transactions", ["symbol"])
    op.create_index("ix_transactions_kind", "transactions", ["kind"])
    op.create_index("ix_transactions_traded_on", "transactions", ["traded_on"])
    op.create_index("ix_transactions_user_symbol", "transactions", ["user_id", "symbol"])
    op.create_index("ix_transactions_user_traded_on", "transactions", ["user_id", "traded_on"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("entity", sa.String(), nullable=False, server_default=""),
        sa.Column("entity_id", sa.String(), nullable=True),
        sa.Column("summary", sa.String(), nullable=False, server_default=""),
        sa.Column("detail", sa.String(), nullable=False, server_default="{}"),
        sa.Column("occurred_at", sa.Float(), nullable=False),
    )
    op.create_index("ix_audit_log_user_id", "audit_log", ["user_id"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])
    op.create_index("ix_audit_log_occurred_at", "audit_log", ["occurred_at"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("transactions")
    op.drop_table("instruments")
