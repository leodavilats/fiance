from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0016_rodada"
down_revision = "0015_rendimento_estimado"
branch_labels = None
depends_on = None

S = "mercado"


def upgrade() -> None:
    op.create_table(
        "rodada",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("iniciada_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("terminada_em", sa.DateTime(timezone=True)),
        sa.Column("falhas", postgresql.JSONB, nullable=False, server_default="{}"),
        schema=S,
    )


def downgrade() -> None:
    op.drop_table("rodada", schema=S)
