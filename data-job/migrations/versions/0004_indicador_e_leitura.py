from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_indicador_e_leitura"
down_revision = "0003_demonstracoes"
branch_labels = None
depends_on = None

S = "mercado"
LEITURA = "mercado_leitura"


def upgrade() -> None:
    op.create_table(
        "indicador",
        sa.Column("serie", sa.Integer, primary_key=True),
        sa.Column("data", sa.Date, primary_key=True),
        sa.Column("valor", sa.Numeric, nullable=False),
        sa.Column("coleta_id", sa.BigInteger, sa.ForeignKey(f"{S}.coleta.id"), nullable=False),
        schema=S,
    )

    # O papel é do cluster e sobrevive ao schema; o usuário com senha entra nele quando houver
    # consumidor: CREATE ROLE <nome> LOGIN PASSWORD '...' IN ROLE mercado_leitura.
    op.execute(
        f"DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{LEITURA}') "
        f"THEN CREATE ROLE {LEITURA} NOLOGIN; END IF; END $$"
    )
    op.execute(f"GRANT USAGE ON SCHEMA {S} TO {LEITURA}")
    op.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {S} TO {LEITURA}")
    op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {S} GRANT SELECT ON TABLES TO {LEITURA}")


def downgrade() -> None:
    op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {S} REVOKE SELECT ON TABLES FROM {LEITURA}")
    op.execute(f"REVOKE SELECT ON ALL TABLES IN SCHEMA {S} FROM {LEITURA}")
    op.execute(f"REVOKE USAGE ON SCHEMA {S} FROM {LEITURA}")
    op.drop_table("indicador", schema=S)
