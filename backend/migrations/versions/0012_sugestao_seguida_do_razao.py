from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012_sugestao_seguida_do_razao"
down_revision = "0011_nivel_de_detalhe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("followed_suggestions") as tabela:
        tabela.add_column(sa.Column("ledger_entry_id", sa.Integer(), nullable=True))
        tabela.create_index(
            "ix_followed_suggestions_ledger_entry_id", ["ledger_entry_id"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("followed_suggestions") as tabela:
        tabela.drop_index("ix_followed_suggestions_ledger_entry_id")
        tabela.drop_column("ledger_entry_id")
