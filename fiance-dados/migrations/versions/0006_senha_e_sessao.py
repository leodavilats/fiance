from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_senha_e_sessao"
down_revision = "0005_anual_parcelado"
branch_labels = None
depends_on = None

S = "acesso"


# A pessoa entra em Minha conta por e-mail e senha; a chave fica para a máquina (ADR-036). Conta sem
# senha ainda entra pela chave, até definir uma. A sessão, como a chave, só é guardada em hash.
def upgrade() -> None:
    op.add_column("conta", sa.Column("senha_hash", sa.Text), schema=S)
    op.create_table(
        "sessao",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("conta_id", sa.BigInteger, sa.ForeignKey(f"{S}.conta.id"), nullable=False),
        sa.Column("hash", sa.Text, nullable=False, unique=True),
        sa.Column(
            "criada_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        schema=S,
    )
    op.create_index("ix_sessao_conta", "sessao", ["conta_id"], schema=S)


def downgrade() -> None:
    op.drop_table("sessao", schema=S)
    op.drop_column("conta", "senha_hash", schema=S)
