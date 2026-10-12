from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0014_tesouro"
down_revision = "0013_fundo_pela_especie"
branch_labels = None
depends_on = None

S = "mercado"


def upgrade() -> None:
    op.create_table(
        "tesouro",
        sa.Column("titulo", sa.Text, primary_key=True),
        sa.Column("vencimento", sa.Date, primary_key=True),
        sa.Column("data", sa.Date, primary_key=True),
        sa.Column("taxa_compra", sa.Numeric),
        sa.Column("taxa_venda", sa.Numeric),
        sa.Column("pu_compra", sa.Numeric),
        sa.Column("pu_venda", sa.Numeric),
        sa.Column("pu_base", sa.Numeric),
        sa.Column("coleta_id", sa.BigInteger, sa.ForeignKey(f"{S}.coleta.id"), nullable=False),
        schema=S,
    )


def downgrade() -> None:
    op.drop_table("tesouro", schema=S)
