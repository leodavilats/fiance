"""Sugestões seguidas Ja existiam ClosedTradeDb (com IR realizado), /rebalance-suggestions e reduce_suggestions."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_followed"
down_revision = "0005_dividends"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "followed_suggestions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("followed_on", sa.String(), nullable=False),
        sa.Column("score_at_suggestion", sa.Float(), nullable=True),
        sa.Column("verdict_at_suggestion", sa.String(), nullable=True),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("followed_suggestions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_followed_suggestions_user_id"), ["user_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_followed_suggestions_ticker"), ["ticker"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_followed_suggestions_followed_on"), ["followed_on"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("followed_suggestions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_followed_suggestions_followed_on"))
        batch_op.drop_index(batch_op.f("ix_followed_suggestions_ticker"))
        batch_op.drop_index(batch_op.f("ix_followed_suggestions_user_id"))
    op.drop_table("followed_suggestions")
