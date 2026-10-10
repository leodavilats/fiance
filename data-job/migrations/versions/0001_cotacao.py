from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_cotacao"
down_revision = None
branch_labels = None
depends_on = None

S = "mercado"


def upgrade() -> None:
    op.create_table(
        "coleta",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("fonte", sa.Text, nullable=False),
        sa.Column("arquivo", sa.Text, nullable=False),
        sa.Column("hash", sa.Text),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("iniciada_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("terminada_em", sa.DateTime(timezone=True)),
        sa.Column("linhas_lidas", sa.Integer),
        sa.Column("linhas_gravadas", sa.Integer),
        sa.Column("linhas_quarentena", sa.Integer),
        sa.Column("erro", sa.Text),
        sa.CheckConstraint(
            "status IN ('rodando', 'ok', 'falhou', 'pulada')", name="ck_coleta_status"
        ),
        schema=S,
    )
    op.create_index("ix_coleta_fonte_hash", "coleta", ["fonte", "hash"], schema=S)

    op.create_table(
        "quarentena",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("coleta_id", sa.BigInteger, sa.ForeignKey(f"{S}.coleta.id"), nullable=False),
        sa.Column("chave", sa.Text, nullable=False),
        sa.Column("motivo", sa.Text, nullable=False),
        sa.Column("conteudo", sa.Text, nullable=False),
        schema=S,
    )
    op.create_index("ix_quarentena_coleta_id", "quarentena", ["coleta_id"], schema=S)

    op.create_table(
        "ativo",
        sa.Column("isin", sa.Text, primary_key=True),
        sa.Column("nome_resumido", sa.Text, nullable=False),
        sa.Column("especie", sa.Text, nullable=False),
        sa.Column("codbdi", sa.Text, nullable=False),
        sa.Column("primeiro_pregao", sa.Date, nullable=False),
        sa.Column("ultimo_pregao", sa.Date, nullable=False),
        schema=S,
    )

    op.create_table(
        "ticker",
        sa.Column("codigo", sa.Text, primary_key=True),
        sa.Column("isin", sa.Text, sa.ForeignKey(f"{S}.ativo.isin"), primary_key=True),
        sa.Column("primeiro_pregao", sa.Date, nullable=False),
        sa.Column("ultimo_pregao", sa.Date, nullable=False),
        schema=S,
    )

    op.create_table(
        "cotacao",
        sa.Column("isin", sa.Text, sa.ForeignKey(f"{S}.ativo.isin"), primary_key=True),
        sa.Column("data", sa.Date, primary_key=True),
        sa.Column("codigo", sa.Text, nullable=False),
        sa.Column("codbdi", sa.Text, nullable=False),
        sa.Column("abertura", sa.Numeric(18, 2), nullable=False),
        sa.Column("maxima", sa.Numeric(18, 2), nullable=False),
        sa.Column("minima", sa.Numeric(18, 2), nullable=False),
        sa.Column("media", sa.Numeric(18, 2), nullable=False),
        sa.Column("fechamento", sa.Numeric(18, 2), nullable=False),
        sa.Column("negocios", sa.Integer, nullable=False),
        sa.Column("quantidade", sa.BigInteger, nullable=False),
        sa.Column("volume", sa.Numeric(22, 2), nullable=False),
        sa.Column("fator_cotacao", sa.Integer, nullable=False),
        sa.Column("coleta_id", sa.BigInteger, sa.ForeignKey(f"{S}.coleta.id"), nullable=False),
        schema=S,
    )
    op.create_index("ix_cotacao_data", "cotacao", ["data"], schema=S)


def downgrade() -> None:
    op.drop_table("cotacao", schema=S)
    op.drop_table("ticker", schema=S)
    op.drop_table("ativo", schema=S)
    op.drop_table("quarentena", schema=S)
    op.drop_table("coleta", schema=S)
