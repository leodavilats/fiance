from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_empresa"
down_revision = "0001_cotacao"
branch_labels = None
depends_on = None

S = "mercado"


def _coleta() -> sa.Column:
    return sa.Column("coleta_id", sa.BigInteger, sa.ForeignKey(f"{S}.coleta.id"), nullable=False)


def upgrade() -> None:
    op.create_table(
        "empresa",
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
        _coleta(),
        schema=S,
    )

    op.create_table(
        "valor_mobiliario",
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
        _coleta(),
        schema=S,
    )
    op.create_index("ix_valor_mobiliario_codigo", "valor_mobiliario", ["codigo"], schema=S)

    op.create_table(
        "emissor_b3",
        sa.Column("codigo", sa.Text, primary_key=True),
        sa.Column("cnpj", sa.Text),
        sa.Column("codigo_cvm", sa.Text),
        sa.Column("razao_social", sa.Text, nullable=False),
        sa.Column("nome_pregao", sa.Text),
        sa.Column("segmento", sa.Text),
        sa.Column("tipo", sa.Text),
        sa.Column("data_listagem", sa.Date),
        _coleta(),
        schema=S,
    )

    op.create_table(
        "emissor",
        sa.Column("codigo", sa.Text, primary_key=True),
        sa.Column("cnpj", sa.Text, nullable=False),
        sa.Column("metodo", sa.Text, nullable=False),
        sa.CheckConstraint("metodo IN ('fca', 'b3', 'nome')", name="ck_emissor_metodo"),
        schema=S,
    )
    op.create_index("ix_emissor_cnpj", "emissor", ["cnpj"], schema=S)


def downgrade() -> None:
    op.drop_table("emissor", schema=S)
    op.drop_table("emissor_b3", schema=S)
    op.drop_table("valor_mobiliario", schema=S)
    op.drop_table("empresa", schema=S)
