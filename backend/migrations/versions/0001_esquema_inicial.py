from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_esquema_inicial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("entity", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=True),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("detail", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("audit_log", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_audit_log_action"), ["action"], unique=False)
        batch_op.create_index(batch_op.f("ix_audit_log_occurred_at"), ["occurred_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_audit_log_user_id"), ["user_id"], unique=False)

    op.create_table(
        "instruments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("asset_type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("isin", sa.String(), nullable=True),
        sa.Column("valid_from", sa.String(), nullable=False),
        sa.Column("valid_to", sa.String(), nullable=True),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("instruments", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_instruments_symbol"), ["symbol"], unique=False)

    op.create_table(
        "job_locks",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("holder", sa.String(), nullable=False),
        sa.Column("acquired_at", sa.Float(), nullable=False),
        sa.Column("expires_at", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("name"),
    )
    op.create_table(
        "processed_webhooks",
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("processed_at", sa.Float(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("provider", "event_id"),
    )
    op.create_table(
        "product_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.Float(), nullable=False),
        sa.Column("day", sa.String(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("props", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("product_events", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_product_events_day"), ["day"], unique=False)
        batch_op.create_index(batch_op.f("ix_product_events_name"), ["name"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_product_events_occurred_at"), ["occurred_at"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_product_events_user_id"), ["user_id"], unique=False)
        batch_op.create_index("ix_product_events_user_name", ["user_id", "name"], unique=False)

    op.create_table(
        "referral_codes",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
    )
    with op.batch_alter_table("referral_codes", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_referral_codes_code"), ["code"], unique=True)

    op.create_table(
        "referrals",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("referred_user_id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.Column("qualified_at", sa.Float(), nullable=True),
        sa.Column("rewarded_at", sa.Float(), nullable=True),
        sa.Column("reward_days", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("referrals", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_referrals_code"), ["code"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_referrals_referred_user_id"), ["referred_user_id"], unique=True
        )
        batch_op.create_index(batch_op.f("ix_referrals_user_id"), ["user_id"], unique=False)

    op.create_table(
        "revoked_tokens",
        sa.Column("jti", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("revoked_at", sa.Float(), nullable=False),
        sa.Column("expires_at", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("jti"),
    )
    with op.batch_alter_table("revoked_tokens", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_revoked_tokens_expires_at"), ["expires_at"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_revoked_tokens_user_id"), ["user_id"], unique=False)

    op.create_table(
        "session_cuts",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("cut_at", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "subscriptions",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("plan_code", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("interval", sa.String(), nullable=False),
        sa.Column("locked", sa.Boolean(), nullable=False),
        sa.Column("granted_at", sa.Float(), nullable=True),
        sa.Column("credited_until", sa.Float(), nullable=True),
        sa.Column("credited_days_total", sa.Integer(), nullable=False),
        sa.Column("trial_started_at", sa.Float(), nullable=True),
        sa.Column("trial_ends_at", sa.Float(), nullable=True),
        sa.Column("current_period_end", sa.Float(), nullable=True),
        sa.Column("cancelled_at", sa.Float(), nullable=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
    )
    with op.batch_alter_table("subscriptions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_subscriptions_external_id"), ["external_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_subscriptions_status"), ["status"], unique=False)

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=True),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("fees", sa.Float(), nullable=False),
        sa.Column("ratio_from", sa.Float(), nullable=False),
        sa.Column("ratio_to", sa.Float(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("traded_on", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_transactions_instrument_id"), ["instrument_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_transactions_kind"), ["kind"], unique=False)
        batch_op.create_index(batch_op.f("ix_transactions_symbol"), ["symbol"], unique=False)
        batch_op.create_index(batch_op.f("ix_transactions_traded_on"), ["traded_on"], unique=False)
        batch_op.create_index(batch_op.f("ix_transactions_user_id"), ["user_id"], unique=False)
        batch_op.create_index("ix_transactions_user_symbol", ["user_id", "symbol"], unique=False)
        batch_op.create_index(
            "ix_transactions_user_traded_on", ["user_id", "traded_on"], unique=False
        )

    op.create_table(
        "usage_counters",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("resource", sa.String(), nullable=False),
        sa.Column("window_key", sa.String(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "resource", "window_key"),
    )
    with op.batch_alter_table("usage_counters", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_usage_counters_expires_at"), ["expires_at"], unique=False
        )

    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("picture", sa.String(), nullable=False),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.Column("onboarded_at", sa.Float(), nullable=True),
        sa.Column("deleted_at", sa.Float(), nullable=True),
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
        sa.Column("loss_offset_used", sa.Float(), nullable=False),
        sa.Column("taxable_profit", sa.Float(), nullable=False),
        sa.Column("loss_compensable", sa.Boolean(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("dividends_received", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_dividends_received_paid_at"), ["paid_at"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_dividends_received_ticker"), ["ticker"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_dividends_received_user_id"), ["user_id"], unique=False
        )

    op.create_table(
        "fixed_income_positions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("valor_investido", sa.Float(), nullable=False),
        sa.Column("taxa", sa.Float(), nullable=False),
        sa.Column("tipo_taxa", sa.String(), nullable=False),
        sa.Column("percentual_cdi", sa.Float(), nullable=True),
        sa.Column("data_aplicacao", sa.String(), nullable=False),
        sa.Column("vencimento", sa.String(), nullable=True),
        sa.Column("liquidez", sa.String(), nullable=False),
        sa.Column("isento_ir", sa.Boolean(), nullable=True),
        sa.Column("oculto", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("fixed_income_positions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_fixed_income_positions_user_id"), ["user_id"], unique=False
        )

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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("followed_suggestions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_followed_suggestions_followed_on"), ["followed_on"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_followed_suggestions_ticker"), ["ticker"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_followed_suggestions_user_id"), ["user_id"], unique=False
        )

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
        sa.Column("density", sa.String(), nullable=False),
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
    with op.batch_alter_table("followed_suggestions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_followed_suggestions_user_id"))
        batch_op.drop_index(batch_op.f("ix_followed_suggestions_ticker"))
        batch_op.drop_index(batch_op.f("ix_followed_suggestions_followed_on"))

    op.drop_table("followed_suggestions")
    with op.batch_alter_table("fixed_income_positions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_fixed_income_positions_user_id"))

    op.drop_table("fixed_income_positions")
    with op.batch_alter_table("dividends_received", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_dividends_received_user_id"))
        batch_op.drop_index(batch_op.f("ix_dividends_received_ticker"))
        batch_op.drop_index(batch_op.f("ix_dividends_received_paid_at"))

    op.drop_table("dividends_received")
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
    with op.batch_alter_table("usage_counters", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_usage_counters_expires_at"))

    op.drop_table("usage_counters")
    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.drop_index("ix_transactions_user_traded_on")
        batch_op.drop_index("ix_transactions_user_symbol")
        batch_op.drop_index(batch_op.f("ix_transactions_user_id"))
        batch_op.drop_index(batch_op.f("ix_transactions_traded_on"))
        batch_op.drop_index(batch_op.f("ix_transactions_symbol"))
        batch_op.drop_index(batch_op.f("ix_transactions_kind"))
        batch_op.drop_index(batch_op.f("ix_transactions_instrument_id"))

    op.drop_table("transactions")
    with op.batch_alter_table("subscriptions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_subscriptions_status"))
        batch_op.drop_index(batch_op.f("ix_subscriptions_external_id"))

    op.drop_table("subscriptions")
    op.drop_table("session_cuts")
    with op.batch_alter_table("revoked_tokens", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_revoked_tokens_user_id"))
        batch_op.drop_index(batch_op.f("ix_revoked_tokens_expires_at"))

    op.drop_table("revoked_tokens")
    with op.batch_alter_table("referrals", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_referrals_user_id"))
        batch_op.drop_index(batch_op.f("ix_referrals_referred_user_id"))
        batch_op.drop_index(batch_op.f("ix_referrals_code"))

    op.drop_table("referrals")
    with op.batch_alter_table("referral_codes", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_referral_codes_code"))

    op.drop_table("referral_codes")
    with op.batch_alter_table("product_events", schema=None) as batch_op:
        batch_op.drop_index("ix_product_events_user_name")
        batch_op.drop_index(batch_op.f("ix_product_events_user_id"))
        batch_op.drop_index(batch_op.f("ix_product_events_occurred_at"))
        batch_op.drop_index(batch_op.f("ix_product_events_name"))
        batch_op.drop_index(batch_op.f("ix_product_events_day"))

    op.drop_table("product_events")
    op.drop_table("processed_webhooks")
    op.drop_table("job_locks")
    with op.batch_alter_table("instruments", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_instruments_symbol"))

    op.drop_table("instruments")
    with op.batch_alter_table("audit_log", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_audit_log_user_id"))
        batch_op.drop_index(batch_op.f("ix_audit_log_occurred_at"))
        batch_op.drop_index(batch_op.f("ix_audit_log_action"))

    op.drop_table("audit_log")
