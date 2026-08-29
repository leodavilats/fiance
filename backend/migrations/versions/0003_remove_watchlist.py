from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_remove_watchlist"
down_revision = "0002_dinheiro_exato"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("watchlist")


def downgrade() -> None:
    op.create_table(
        "watchlist",
        sa.Column("user_id", sa.VARCHAR(), nullable=False),
        sa.Column("ticker", sa.VARCHAR(), nullable=False),
        sa.Column("note", sa.VARCHAR(), nullable=False),
        sa.Column("created_at", sa.FLOAT(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "ticker"),
    )
