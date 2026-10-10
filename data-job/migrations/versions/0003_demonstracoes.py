from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_demonstracoes"
down_revision = "0002_empresa"
branch_labels = None
depends_on = None

S = "mercado"


def upgrade() -> None:
    op.create_table(
        "documento",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("cnpj", sa.Text, nullable=False),
        sa.Column("tipo", sa.Text, nullable=False),
        sa.Column("data_referencia", sa.Date, nullable=False),
        sa.Column("versao", sa.Integer, nullable=False),
        sa.Column("codigo_cvm", sa.Text),
        sa.Column("id_documento", sa.Text),
        sa.Column("data_entrega", sa.Date),
        sa.Column("coleta_id", sa.BigInteger, sa.ForeignKey(f"{S}.coleta.id"), nullable=False),
        sa.UniqueConstraint("cnpj", "tipo", "data_referencia", "versao", name="uq_documento"),
        sa.CheckConstraint("tipo IN ('DFP', 'ITR')", name="ck_documento_tipo"),
        schema=S,
    )

    op.create_table(
        "demonstracao_linha",
        sa.Column(
            "documento_id", sa.BigInteger, sa.ForeignKey(f"{S}.documento.id"), primary_key=True
        ),
        sa.Column("demonstracao", sa.Text, primary_key=True),
        sa.Column("inicio_exercicio", sa.Date, primary_key=True),
        sa.Column("fim_exercicio", sa.Date, primary_key=True),
        sa.Column("conta", sa.Text, primary_key=True),
        sa.Column("consolidado", sa.Boolean, nullable=False),
        sa.Column("descricao", sa.Text, nullable=False),
        sa.Column("valor", sa.Numeric, nullable=False),
        sa.Column("conta_fixa", sa.Boolean, nullable=False),
        sa.Column("coleta_id", sa.BigInteger, sa.ForeignKey(f"{S}.coleta.id"), nullable=False),
        schema=S,
    )


def downgrade() -> None:
    op.drop_table("demonstracao_linha", schema=S)
    op.drop_table("documento", schema=S)
