from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_anual_parcelado"
down_revision = "0004_pagamento"
branch_labels = None
depends_on = None

S = "acesso"


# O anual parcelado no cartão é um parcelamento do Asaas, não uma assinatura: asaas_assinatura guarda
# o id do parcelamento, e o ano pago conta do início, não do vencimento de cada parcela (ADR-035).
def upgrade() -> None:
    op.add_column("assinatura", sa.Column("parcelas", sa.SmallInteger), schema=S)
    op.add_column("assinatura", sa.Column("inicio", sa.Date), schema=S)
    op.create_check_constraint(
        "ck_assinatura_parcelado",
        "assinatura",
        "parcelas IS NULL OR (ciclo = 'anual' AND parcelas BETWEEN 2 AND 21 AND inicio IS NOT NULL)",
        schema=S,
    )


def downgrade() -> None:
    op.drop_constraint("ck_assinatura_parcelado", "assinatura", schema=S)
    op.drop_column("assinatura", "inicio", schema=S)
    op.drop_column("assinatura", "parcelas", schema=S)
