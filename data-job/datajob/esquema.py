from __future__ import annotations

import sqlalchemy as sa

SCHEMA = "mercado"

metadata = sa.MetaData(schema=SCHEMA)

coleta = sa.Table(
    "coleta",
    metadata,
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
    sa.CheckConstraint("status IN ('rodando', 'ok', 'falhou', 'pulada')", name="ck_coleta_status"),
)
sa.Index("ix_coleta_fonte_hash", coleta.c.fonte, coleta.c.hash)

quarentena = sa.Table(
    "quarentena",
    metadata,
    sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
    sa.Column("coleta_id", sa.BigInteger, sa.ForeignKey("coleta.id"), nullable=False),
    sa.Column("chave", sa.Text, nullable=False),
    sa.Column("motivo", sa.Text, nullable=False),
    sa.Column("conteudo", sa.Text, nullable=False),
)
sa.Index("ix_quarentena_coleta_id", quarentena.c.coleta_id)

ativo = sa.Table(
    "ativo",
    metadata,
    sa.Column("isin", sa.Text, primary_key=True),
    sa.Column("nome_resumido", sa.Text, nullable=False),
    sa.Column("especie", sa.Text, nullable=False),
    sa.Column("codbdi", sa.Text, nullable=False),
    sa.Column("primeiro_pregao", sa.Date, nullable=False),
    sa.Column("ultimo_pregao", sa.Date, nullable=False),
)

ticker = sa.Table(
    "ticker",
    metadata,
    sa.Column("codigo", sa.Text, primary_key=True),
    sa.Column("isin", sa.Text, sa.ForeignKey("ativo.isin"), primary_key=True),
    sa.Column("primeiro_pregao", sa.Date, nullable=False),
    sa.Column("ultimo_pregao", sa.Date, nullable=False),
)

cotacao = sa.Table(
    "cotacao",
    metadata,
    sa.Column("isin", sa.Text, sa.ForeignKey("ativo.isin"), primary_key=True),
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
    sa.Column("coleta_id", sa.BigInteger, sa.ForeignKey("coleta.id"), nullable=False),
)
sa.Index("ix_cotacao_data", cotacao.c.data)
