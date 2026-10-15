from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_planos_pagos"
down_revision = "0001_acesso"
branch_labels = None
depends_on = None

S = "acesso"
TODOS = ["serie", "ponto_no_tempo", "informes", "exportacao"]

# Nenhum plano gratuito (ADR-025). Preço em centavos; vazio é plano sem cobrança (interno, convidado).
_PAGOS = [
    {
        "codigo": "essencial",
        "nome": "Essencial",
        "descricao": "Cotação, proventos, retrato do ativo e macro dos últimos dois anos.",
        "limite_por_minuto": 30,
        "limite_por_dia": 5_000,
        "historico_dias": 730,
        "chaves_maximas": 2,
        "preco_mensal_centavos": 4_900,
        "preco_anual_centavos": 49_000,
        "recursos": [],
        "ordem": 1,
    },
    {
        "codigo": "pro",
        "nome": "Pro",
        "descricao": "O histórico inteiro, a série ajustada, os balanços como se sabia na data e o informe de FII.",
        "limite_por_minuto": 60,
        "limite_por_dia": 30_000,
        "historico_dias": None,
        "chaves_maximas": 5,
        "preco_mensal_centavos": 14_900,
        "preco_anual_centavos": 149_000,
        "recursos": ["serie", "ponto_no_tempo", "informes"],
        "ordem": 2,
    },
    {
        "codigo": "quant",
        "nome": "Quant",
        "descricao": "Tudo, com limites altos, exportação da base e uso comercial interno, sob contrato.",
        "limite_por_minuto": 300,
        "limite_por_dia": 300_000,
        "historico_dias": None,
        "chaves_maximas": 20,
        "preco_mensal_centavos": 49_000,
        "preco_anual_centavos": None,
        "recursos": TODOS,
        "ordem": 3,
    },
]


def upgrade() -> None:
    op.add_column("plano", sa.Column("descricao", sa.Text), schema=S)
    op.add_column("plano", sa.Column("preco_mensal_centavos", sa.Integer), schema=S)
    op.add_column("plano", sa.Column("preco_anual_centavos", sa.Integer), schema=S)
    op.add_column(
        "plano",
        sa.Column("recursos", postgresql.ARRAY(sa.Text), nullable=False, server_default="{}"),
        schema=S,
    )
    op.add_column(
        "plano",
        sa.Column("publico", sa.Boolean, nullable=False, server_default=sa.false()),
        schema=S,
    )
    op.add_column(
        "plano", sa.Column("ordem", sa.Integer, nullable=False, server_default="0"), schema=S
    )
    op.execute(
        f"UPDATE {S}.plano SET recursos = ARRAY{TODOS!r}::text[] "
        "WHERE codigo IN ('interno', 'convidado')"
    )
    plano = sa.table(
        "plano",
        *(
            sa.column(c)
            for c in (
                "codigo", "nome", "descricao", "limite_por_minuto", "limite_por_dia",
                "historico_dias", "chaves_maximas", "preco_mensal_centavos",
                "preco_anual_centavos", "recursos", "ordem", "publico",
            )
        ),
        schema=S,
    )  # fmt: skip
    op.bulk_insert(plano, [{**p, "publico": True} for p in _PAGOS])
    op.execute(f"UPDATE {S}.conta SET plano = 'convidado' WHERE plano = 'gratuito'")
    op.execute(f"DELETE FROM {S}.plano WHERE codigo = 'gratuito'")

    op.add_column("conta", sa.Column("pago_ate", sa.Date), schema=S)
    op.create_table(
        "assinatura",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("conta_id", sa.BigInteger, sa.ForeignKey(f"{S}.conta.id"), nullable=False),
        sa.Column("plano", sa.Text, sa.ForeignKey(f"{S}.plano.codigo"), nullable=False),
        sa.Column("ciclo", sa.Text, nullable=False),
        sa.Column("asaas_cliente", sa.Text, nullable=False),
        sa.Column("asaas_assinatura", sa.Text, nullable=False, unique=True),
        sa.Column("situacao", sa.Text, nullable=False, server_default="aguardando"),
        sa.Column(
            "criada_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("ciclo IN ('mensal', 'anual')", name="ck_assinatura_ciclo"),
        schema=S,
    )
    op.create_table(
        "evento_de_cobranca",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("tipo", sa.Text, nullable=False),
        sa.Column(
            "recebido_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("resultado", sa.Text),
        schema=S,
    )


def downgrade() -> None:
    raise NotImplementedError(
        "o plano gratuito saiu por decisão (ADR-025), e não volta por migração"
    )
