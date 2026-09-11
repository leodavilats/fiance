from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009_sem_landing"
down_revision = "0008_caixa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("interest_signups")


def downgrade() -> None:
    op.create_table(
        "interest_signups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interest_signups_email", "interest_signups", ["email"], unique=True)
