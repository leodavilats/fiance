"""Lock cooperativo para jobs de background Os jobs do startup rodavam em todo worker: com mais de um worker/dyno, cada um executava o ciclo de notificação, gerando pushes duplicados."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_job_locks"
down_revision = "0002_fixed_income"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_locks",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("holder", sa.String(), nullable=False),
        sa.Column("acquired_at", sa.Float(), nullable=False),
        sa.Column("expires_at", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("name"),
    )


def downgrade() -> None:
    op.drop_table("job_locks")
