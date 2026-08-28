"""Revogacao de sessao, contadores de uso e eventos de produto (G0)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008_session_usage_events"
down_revision = "0007_loss_compensable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("onboarded_at", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("deleted_at", sa.Float(), nullable=True))

    op.create_table(
        "session_cuts",
        sa.Column("user_id", sa.String(), primary_key=True),
        sa.Column("cut_at", sa.Float(), nullable=False),
    )

    op.create_table(
        "revoked_tokens",
        sa.Column("jti", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("revoked_at", sa.Float(), nullable=False),
        sa.Column("expires_at", sa.Float(), nullable=False),
    )
    op.create_index("ix_revoked_tokens_user_id", "revoked_tokens", ["user_id"])
    op.create_index("ix_revoked_tokens_expires_at", "revoked_tokens", ["expires_at"])

    op.create_table(
        "usage_counters",
        sa.Column("user_id", sa.String(), primary_key=True),
        sa.Column("resource", sa.String(), primary_key=True),
        sa.Column("window_key", sa.String(), primary_key=True),
        sa.Column("count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("expires_at", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.Float(), nullable=False),
    )
    op.create_index("ix_usage_counters_expires_at", "usage_counters", ["expires_at"])

    op.create_table(
        "product_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.Float(), nullable=False),
        sa.Column("day", sa.String(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False, server_default="web"),
        sa.Column("props", sa.String(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_product_events_user_id", "product_events", ["user_id"])
    op.create_index("ix_product_events_name", "product_events", ["name"])
    op.create_index("ix_product_events_occurred_at", "product_events", ["occurred_at"])
    op.create_index("ix_product_events_day", "product_events", ["day"])
    op.create_index("ix_product_events_user_name", "product_events", ["user_id", "name"])


def downgrade() -> None:
    op.drop_table("product_events")
    op.drop_table("usage_counters")
    op.drop_table("revoked_tokens")
    op.drop_table("session_cuts")
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("deleted_at")
        batch_op.drop_column("onboarded_at")
