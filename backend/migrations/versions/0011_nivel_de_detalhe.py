from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011_nivel_de_detalhe"
down_revision = "0010_alvo_de_reserva"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("preferences") as tabela:
        tabela.add_column(
            sa.Column("detail_level", sa.String(), nullable=False, server_default="completo")
        )
        tabela.drop_column("density")


def downgrade() -> None:
    with op.batch_alter_table("preferences") as tabela:
        tabela.add_column(
            sa.Column("density", sa.String(), nullable=False, server_default="comfortable")
        )
        tabela.drop_column("detail_level")
