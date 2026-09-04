from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_sessoes_de_checkout"
down_revision = "0004_cache_no_banco"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "checkout_sessions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False, server_default="none"),
        sa.Column("plan_code", sa.String(), nullable=False, server_default="premium"),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("interval", sa.String(), nullable=False, server_default="monthly"),
        sa.Column("created_at", sa.Float(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_checkout_sessions_user_id", "checkout_sessions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_checkout_sessions_user_id", table_name="checkout_sessions")
    op.drop_table("checkout_sessions")
