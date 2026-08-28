"""Assinatura com preco travado e webhooks idempotentes (G3)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011_subscriptions"
down_revision = "0010_preferences_density"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("user_id", sa.String(), primary_key=True),
        sa.Column("plan_code", sa.String(), nullable=False, server_default="free"),
        sa.Column("status", sa.String(), nullable=False, server_default="none"),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("currency", sa.String(), nullable=False, server_default="BRL"),
        sa.Column("interval", sa.String(), nullable=False, server_default="monthly"),
        sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("granted_at", sa.Float(), nullable=True),
        sa.Column("trial_started_at", sa.Float(), nullable=True),
        sa.Column("trial_ends_at", sa.Float(), nullable=True),
        sa.Column("current_period_end", sa.Float(), nullable=True),
        sa.Column("cancelled_at", sa.Float(), nullable=True),
        sa.Column("provider", sa.String(), nullable=False, server_default="none"),
        sa.Column("external_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_at", sa.Float(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])
    op.create_index("ix_subscriptions_external_id", "subscriptions", ["external_id"])

    op.create_table(
        "processed_webhooks",
        sa.Column("provider", sa.String(), primary_key=True),
        sa.Column("event_id", sa.String(), primary_key=True),
        sa.Column("processed_at", sa.Float(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_table("processed_webhooks")
    op.drop_table("subscriptions")
