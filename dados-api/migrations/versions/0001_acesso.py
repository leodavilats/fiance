from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_acesso"
down_revision = None
branch_labels = None
depends_on = None

S = "acesso"

# historico_dias vazio é o histórico inteiro. O convidado não paga e vê tudo: é quem testa o produto.
_PLANOS = [
    ("interno", "Interno", 600, 1_000_000, None, 10),
    ("convidado", "Convidado", 60, 20_000, None, 3),
    ("gratuito", "Gratuito", 10, 500, 365, 2),
]


def upgrade() -> None:
    plano = op.create_table(
        "plano",
        sa.Column("codigo", sa.Text, primary_key=True),
        sa.Column("nome", sa.Text, nullable=False),
        sa.Column("limite_por_minuto", sa.Integer, nullable=False),
        sa.Column("limite_por_dia", sa.Integer, nullable=False),
        sa.Column("historico_dias", sa.Integer),
        sa.Column("chaves_maximas", sa.Integer, nullable=False),
        schema=S,
    )
    op.bulk_insert(
        plano,
        [
            {
                "codigo": c,
                "nome": n,
                "limite_por_minuto": m,
                "limite_por_dia": d,
                "historico_dias": h,
                "chaves_maximas": k,
            }
            for c, n, m, d, h, k in _PLANOS
        ],
    )
    op.create_table(
        "conta",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("email", sa.Text, nullable=False),
        sa.Column("nome", sa.Text, nullable=False),
        sa.Column("plano", sa.Text, sa.ForeignKey(f"{S}.plano.codigo"), nullable=False),
        sa.Column("ativa", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("observacao", sa.Text),
        sa.Column(
            "criada_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        schema=S,
    )
    op.create_index("ix_conta_email", "conta", [sa.text("lower(email)")], unique=True, schema=S)
    op.create_table(
        "chave",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("conta_id", sa.BigInteger, sa.ForeignKey(f"{S}.conta.id"), nullable=False),
        sa.Column("prefixo", sa.Text, nullable=False, unique=True),
        sa.Column("hash", sa.Text, nullable=False, unique=True),
        sa.Column("nome", sa.Text, nullable=False),
        sa.Column(
            "criada_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("revogada_em", sa.DateTime(timezone=True)),
        sa.Column("ultimo_uso_em", sa.DateTime(timezone=True)),
        schema=S,
    )
    op.create_table(
        "uso_diario",
        sa.Column("chave_id", sa.BigInteger, sa.ForeignKey(f"{S}.chave.id"), primary_key=True),
        sa.Column("dia", sa.Date, primary_key=True),
        sa.Column("requisicoes", sa.Integer, nullable=False),
        schema=S,
    )


def downgrade() -> None:
    for tabela in ("uso_diario", "chave", "conta", "plano"):
        op.drop_table(tabela, schema=S)
