from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010_alvo_de_reserva"
down_revision = "0009_sem_landing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "preferences",
        sa.Column("reserve_months_target", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("preferences", "reserve_months_target")
