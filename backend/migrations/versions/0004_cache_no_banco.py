from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_cache_no_banco"
down_revision = "0003_remove_watchlist"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cache_entries",
        sa.Column("k", sa.String(), nullable=False),
        sa.Column("v", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("k"),
    )
    op.create_index("ix_cache_entries_expires_at", "cache_entries", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_cache_entries_expires_at", table_name="cache_entries")
    op.drop_table("cache_entries")
