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

empresa = sa.Table(
    "empresa",
    metadata,
    sa.Column("cnpj", sa.Text, primary_key=True),
    sa.Column("codigo_cvm", sa.Text),
    sa.Column("razao_social", sa.Text, nullable=False),
    sa.Column("nome_comercial", sa.Text),
    sa.Column("setor", sa.Text),
    sa.Column("situacao", sa.Text),
    sa.Column("situacao_emissor", sa.Text),
    sa.Column("controle_acionario", sa.Text),
    sa.Column("data_registro", sa.Date),
    sa.Column("data_cancelamento", sa.Date),
    sa.Column("motivo_cancelamento", sa.Text),
    sa.Column("coleta_id", sa.BigInteger, sa.ForeignKey("coleta.id"), nullable=False),
)

valor_mobiliario = sa.Table(
    "valor_mobiliario",
    metadata,
    sa.Column("cnpj", sa.Text, primary_key=True),
    sa.Column("data_referencia", sa.Date, primary_key=True),
    sa.Column("versao", sa.Integer, primary_key=True),
    sa.Column("tipo", sa.Text, primary_key=True),
    sa.Column("classe", sa.Text, primary_key=True),
    sa.Column("codigo", sa.Text, primary_key=True),
    sa.Column("id_documento", sa.Text, nullable=False),
    sa.Column("mercado", sa.Text),
    sa.Column("segmento", sa.Text),
    sa.Column("inicio_negociacao", sa.Date),
    sa.Column("fim_negociacao", sa.Date),
    sa.Column("inicio_listagem", sa.Date),
    sa.Column("fim_listagem", sa.Date),
    sa.Column("coleta_id", sa.BigInteger, sa.ForeignKey("coleta.id"), nullable=False),
)
sa.Index("ix_valor_mobiliario_codigo", valor_mobiliario.c.codigo)

emissor_b3 = sa.Table(
    "emissor_b3",
    metadata,
    sa.Column("codigo", sa.Text, primary_key=True),
    sa.Column("cnpj", sa.Text),
    sa.Column("codigo_cvm", sa.Text),
    sa.Column("razao_social", sa.Text, nullable=False),
    sa.Column("nome_pregao", sa.Text),
    sa.Column("segmento", sa.Text),
    sa.Column("tipo", sa.Text),
    sa.Column("data_listagem", sa.Date),
    sa.Column("coleta_id", sa.BigInteger, sa.ForeignKey("coleta.id"), nullable=False),
)

emissor = sa.Table(
    "emissor",
    metadata,
    sa.Column("codigo", sa.Text, primary_key=True),
    sa.Column("cnpj", sa.Text, nullable=False),
    sa.Column("metodo", sa.Text, nullable=False),
    sa.CheckConstraint("metodo IN ('fca', 'b3', 'nome')", name="ck_emissor_metodo"),
)
sa.Index("ix_emissor_cnpj", emissor.c.cnpj)

documento = sa.Table(
    "documento",
    metadata,
    sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
    sa.Column("cnpj", sa.Text, nullable=False),
    sa.Column("tipo", sa.Text, nullable=False),
    sa.Column("data_referencia", sa.Date, nullable=False),
    sa.Column("versao", sa.Integer, nullable=False),
    sa.Column("codigo_cvm", sa.Text),
    sa.Column("id_documento", sa.Text),
    sa.Column("data_entrega", sa.Date),
    sa.Column("coleta_id", sa.BigInteger, sa.ForeignKey("coleta.id"), nullable=False),
    sa.UniqueConstraint("cnpj", "tipo", "data_referencia", "versao", name="uq_documento"),
    sa.CheckConstraint("tipo IN ('DFP', 'ITR')", name="ck_documento_tipo"),
)

demonstracao_linha = sa.Table(
    "demonstracao_linha",
    metadata,
    sa.Column("documento_id", sa.BigInteger, sa.ForeignKey("documento.id"), primary_key=True),
    sa.Column("demonstracao", sa.Text, primary_key=True),
    sa.Column("inicio_exercicio", sa.Date, primary_key=True),
    sa.Column("fim_exercicio", sa.Date, primary_key=True),
    sa.Column("conta", sa.Text, primary_key=True),
    sa.Column("consolidado", sa.Boolean, nullable=False),
    sa.Column("descricao", sa.Text, nullable=False),
    sa.Column("valor", sa.Numeric, nullable=False),
    sa.Column("conta_fixa", sa.Boolean, nullable=False),
    sa.Column("coleta_id", sa.BigInteger, sa.ForeignKey("coleta.id"), nullable=False),
)

indicador = sa.Table(
    "indicador",
    metadata,
    sa.Column("serie", sa.Integer, primary_key=True),
    sa.Column("data", sa.Date, primary_key=True),
    sa.Column("valor", sa.Numeric, nullable=False),
    sa.Column("coleta_id", sa.BigInteger, sa.ForeignKey("coleta.id"), nullable=False),
)
