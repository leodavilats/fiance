"""Indicacao: codigo, atribuicao e credito de assinatura (G3)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012_referrals"
down_revision = "0011_subscriptions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "referral_codes",
        sa.Column("user_id", sa.String(), primary_key=True),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("created_at", sa.Float(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_referral_codes_code", "referral_codes", ["code"], unique=True)

    op.create_table(
        "referrals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("referred_user_id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("created_at", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("qualified_at", sa.Float(), nullable=True),
        sa.Column("rewarded_at", sa.Float(), nullable=True),
        sa.Column("reward_days", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_referrals_user_id", "referrals", ["user_id"])
    op.create_index("ix_referrals_code", "referrals", ["code"])
    # Unico: uma pessoa e atribuida no maximo uma vez na vida. Sem isso a mesma
    # conta renderia credito a cada amigo que a reivindicasse.
    op.create_index("ix_referrals_referred_user_id", "referrals", ["referred_user_id"], unique=True)

    op.add_column("subscriptions", sa.Column("credited_until", sa.Float(), nullable=True))
    op.add_column(
        "subscriptions",
        sa.Column("credited_days_total", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )


def downgrade() -> None:
    op.drop_column("subscriptions", "credited_days_total")
    op.drop_column("subscriptions", "credited_until")
    op.drop_table("referrals")
    op.drop_table("referral_codes")
