from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_pagamento"
down_revision = "0003_sem_quant"
branch_labels = None
depends_on = None

S = "acesso"


# Cada pagamento aplicado, para o estorno saber até onde recuar o pago_ate, e a assinatura substituída
# que o Asaas ainda não cancelou, para a conferência tentar de novo (ADR-034).
def upgrade() -> None:
    op.create_table(
        "pagamento",
        sa.Column("asaas_pagamento", sa.Text, primary_key=True),
        sa.Column(
            "assinatura_id", sa.BigInteger, sa.ForeignKey(f"{S}.assinatura.id"), nullable=False
        ),
        sa.Column("vence", sa.Date, nullable=False),
        sa.Column("cobre_ate", sa.Date, nullable=False),
        sa.Column("situacao", sa.Text, nullable=False),
        sa.Column(
            "registrado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("situacao IN ('confirmado', 'estornado')", name="ck_pagamento_situacao"),
        schema=S,
    )
    op.create_index("ix_pagamento_assinatura", "pagamento", ["assinatura_id"], schema=S)
    op.add_column(
        "assinatura",
        sa.Column("cancelamento_pendente", sa.Boolean, nullable=False, server_default=sa.false()),
        schema=S,
    )


def downgrade() -> None:
    op.drop_column("assinatura", "cancelamento_pendente", schema=S)
    op.drop_table("pagamento", schema=S)
