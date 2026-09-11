from __future__ import annotations

import sqlalchemy as sa
from alembic import op

import app.core.money

revision = "0008_caixa"
down_revision = "0007_interesse_na_espera"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cash_entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("amount", app.core.money.ExactNumeric(), nullable=False),
        sa.Column("due_on", sa.String(), nullable=False),
        sa.Column("paid_on", sa.String(), nullable=True),
        sa.Column("recurrence_id", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cash_entries_user_id"), "cash_entries", ["user_id"])
    op.create_index(op.f("ix_cash_entries_kind"), "cash_entries", ["kind"])
    op.create_index(op.f("ix_cash_entries_category"), "cash_entries", ["category"])
    op.create_index(op.f("ix_cash_entries_due_on"), "cash_entries", ["due_on"])
    op.create_index(op.f("ix_cash_entries_paid_on"), "cash_entries", ["paid_on"])
    op.create_index(op.f("ix_cash_entries_recurrence_id"), "cash_entries", ["recurrence_id"])
    op.create_index("ix_cash_entries_user_due", "cash_entries", ["user_id", "due_on"])
    op.create_index("ix_cash_entries_user_paid", "cash_entries", ["user_id", "paid_on"])

    op.create_table(
        "cash_recurrences",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("amount", app.core.money.ExactNumeric(), nullable=False),
        sa.Column("day_of_month", sa.Integer(), nullable=False),
        sa.Column("starts_on", sa.String(), nullable=False),
        sa.Column("ends_on", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cash_recurrences_user_id"), "cash_recurrences", ["user_id"])

    op.create_table(
        "debts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("balance", app.core.money.ExactNumeric(), nullable=False),
        sa.Column("monthly_rate", sa.Float(), nullable=True),
        sa.Column("settled_at", sa.Float(), nullable=True),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_debts_user_id"), "debts", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_debts_user_id"), table_name="debts")
    op.drop_table("debts")

    op.drop_index(op.f("ix_cash_recurrences_user_id"), table_name="cash_recurrences")
    op.drop_table("cash_recurrences")

    op.drop_index("ix_cash_entries_user_paid", table_name="cash_entries")
    op.drop_index("ix_cash_entries_user_due", table_name="cash_entries")
    op.drop_index(op.f("ix_cash_entries_recurrence_id"), table_name="cash_entries")
    op.drop_index(op.f("ix_cash_entries_paid_on"), table_name="cash_entries")
    op.drop_index(op.f("ix_cash_entries_due_on"), table_name="cash_entries")
    op.drop_index(op.f("ix_cash_entries_category"), table_name="cash_entries")
    op.drop_index(op.f("ix_cash_entries_kind"), table_name="cash_entries")
    op.drop_index(op.f("ix_cash_entries_user_id"), table_name="cash_entries")
    op.drop_table("cash_entries")
