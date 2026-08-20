"""Baseline do schema

Estado do banco no momento em que o Alembic foi introduzido, para que bancos
já existentes possam ser marcados (`stamp`) nesta revisão em vez de recriados.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-08-20 09:15:21.643931
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("picture", sa.String(), nullable=False),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_users_email"), ["email"], unique=True)

    op.create_table(
        "closed_trades",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("avg_price", sa.Float(), nullable=False),
        sa.Column("sell_price", sa.Float(), nullable=False),
        sa.Column("gross_profit", sa.Float(), nullable=False),
        sa.Column("ir_rate", sa.Float(), nullable=False),
        sa.Column("ir_amount", sa.Float(), nullable=False),
        sa.Column("net_profit", sa.Float(), nullable=False),
        sa.Column("sold_at", sa.Float(), nullable=False),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("closed_trades", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_closed_trades_user_id"), ["user_id"], unique=False)

    op.create_table(
        "device_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("device_tokens", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_device_tokens_token"), ["token"], unique=True)
        batch_op.create_index(batch_op.f("ix_device_tokens_user_id"), ["user_id"], unique=False)

    op.create_table(
        "goals",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("target_pct", sa.Float(), nullable=False),
        sa.Column("target_value", sa.Float(), nullable=True),
        sa.Column("deadline", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "category"),
    )
    op.create_table(
        "notified_opportunities",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("notified_at", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "ticker"),
    )
    op.create_table(
        "portfolio",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("avg_price", sa.Float(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "ticker"),
    )
    op.create_table(
        "portfolio_snapshot",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("captured_at", sa.Float(), nullable=False),
        sa.Column("total_invested", sa.Float(), nullable=False),
        sa.Column("total_current", sa.Float(), nullable=False),
        sa.Column("total_pnl", sa.Float(), nullable=False),
        sa.Column("total_pnl_pct", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "captured_at"),
    )
    op.create_table(
        "preferences",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("cash_available", sa.Float(), nullable=False),
        sa.Column("passive_income_goal", sa.Float(), nullable=True),
        sa.Column("desired_yield_stock", sa.Float(), nullable=False),
        sa.Column("desired_yield_fii", sa.Float(), nullable=False),
        sa.Column("desired_yield_bdr", sa.Float(), nullable=False),
        sa.Column("desired_yield_etf", sa.Float(), nullable=False),
        sa.Column("notify_price_alerts", sa.Boolean(), nullable=False),
        sa.Column("opportunities_frequency", sa.String(), nullable=False),
        sa.Column("risk_profile", sa.String(), nullable=False),
        sa.Column("preferred_categories", sa.String(), nullable=False),
        sa.Column("preferred_sectors", sa.String(), nullable=False),
        sa.Column("excluded_tickers", sa.String(), nullable=False),
        sa.Column("last_digest_sent_at", sa.Float(), nullable=True),
        sa.Column("updated_at", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "price_alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("condition", sa.String(), nullable=False),
        sa.Column("target_price", sa.Float(), nullable=False),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.Column("triggered_at", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("price_alerts", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_price_alerts_user_id"), ["user_id"], unique=False)

    op.create_table(
        "sector_goals",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("sector", sa.String(), nullable=False),
        sa.Column("target_pct", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "sector"),
    )
    op.create_table(
        "watchlist",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("note", sa.String(), nullable=False),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "ticker"),
    )


def downgrade() -> None:
    op.drop_table("watchlist")
    op.drop_table("sector_goals")
    with op.batch_alter_table("price_alerts", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_price_alerts_user_id"))

    op.drop_table("price_alerts")
    op.drop_table("preferences")
    op.drop_table("portfolio_snapshot")
    op.drop_table("portfolio")
    op.drop_table("notified_opportunities")
    op.drop_table("goals")
    with op.batch_alter_table("device_tokens", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_device_tokens_user_id"))
        batch_op.drop_index(batch_op.f("ix_device_tokens_token"))

    op.drop_table("device_tokens")
    with op.batch_alter_table("closed_trades", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_closed_trades_user_id"))

    op.drop_table("closed_trades")
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_email"))

    op.drop_table("users")
