from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007_interesse_na_espera"
down_revision = "0006_remove_closed_trades"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "interest_signups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interest_signups_email"), "interest_signups", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_interest_signups_email"), table_name="interest_signups")
    op.drop_table("interest_signups")
