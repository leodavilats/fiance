from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0017_fii_mensal_e_pagamento"
down_revision = "0016_rodada"
branch_labels = None
depends_on = None

S = "mercado"


def upgrade() -> None:
    op.add_column("provento", sa.Column("data_pagamento", sa.Date), schema=S)
    op.create_table(
        "fii_mensal",
        sa.Column("emissor", sa.Text, primary_key=True),
        sa.Column("classe", sa.Text, primary_key=True),
        sa.Column("referencia", sa.Date, primary_key=True),
        sa.Column("cnpj", sa.Text, nullable=False),
        sa.Column("isin", sa.Text, nullable=False),
        sa.Column("nome", sa.Text),
        sa.Column("segmento", sa.Text),
        sa.Column("mandato", sa.Text),
        sa.Column("valor_patrimonial_cota", sa.Numeric),
        sa.Column("patrimonio_liquido", sa.Numeric),
        sa.Column("cotas_emitidas", sa.Numeric),
        sa.Column("dividend_yield_mes", sa.Numeric),
        sa.Column("coleta_id", sa.BigInteger, sa.ForeignKey(f"{S}.coleta.id"), nullable=False),
        schema=S,
    )


def downgrade() -> None:
    op.drop_table("fii_mensal", schema=S)
    op.drop_column("provento", "data_pagamento", schema=S)
