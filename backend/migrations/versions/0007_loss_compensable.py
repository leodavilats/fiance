"""Prejuizo compensavel: separa perda apurada em operacao isenta."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007_loss_compensable"
down_revision = "0006_followed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("closed_trades", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "loss_compensable",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("closed_trades", schema=None) as batch_op:
        batch_op.drop_column("loss_compensable")
