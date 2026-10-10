from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011_capital_social"
down_revision = "0010_eventos_inferidos"
branch_labels = None
depends_on = None

S = "mercado"


def upgrade() -> None:
    op.create_table(
        "capital_social",
        sa.Column("cnpj", sa.Text, primary_key=True),
        sa.Column("data_referencia", sa.Date, primary_key=True),
        sa.Column("versao", sa.Integer, primary_key=True),
        sa.Column("data_aprovacao", sa.Date, primary_key=True),
        sa.Column("acoes_ordinarias", sa.BigInteger),
        sa.Column("acoes_preferenciais", sa.BigInteger),
        sa.Column("acoes_total", sa.BigInteger, nullable=False),
        sa.Column("coleta_id", sa.BigInteger, sa.ForeignKey(f"{S}.coleta.id"), nullable=False),
        schema=S,
    )


def downgrade() -> None:
    op.drop_table("capital_social", schema=S)
