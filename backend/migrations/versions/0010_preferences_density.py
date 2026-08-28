"""Densidade de tela como preferencia da conta (G2)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010_preferences_density"
down_revision = "0009_ledger_instruments_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("preferences", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "density",
                sa.String(),
                nullable=False,
                server_default="comfortable",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("preferences", schema=None) as batch_op:
        batch_op.drop_column("density")
