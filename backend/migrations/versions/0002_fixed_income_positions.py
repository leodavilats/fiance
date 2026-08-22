"""Renda fixa como entidade de primeira classe Antes taxa, prazo, data de aplicação e % do CDI viviam só no localStorage do navegador; o servidor conhecia apenas o valor investido, num ticker sintético `RF_<tipo>_<índice>`."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_fixed_income"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fixed_income_positions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("valor_investido", sa.Float(), nullable=False),
        sa.Column("taxa", sa.Float(), nullable=False),
        sa.Column("tipo_taxa", sa.String(), nullable=False),
        sa.Column("percentual_cdi", sa.Float(), nullable=True),
        sa.Column("data_aplicacao", sa.String(), nullable=False),
        sa.Column("vencimento", sa.String(), nullable=True),
        sa.Column("liquidez", sa.String(), nullable=False),
        sa.Column("isento_ir", sa.Boolean(), nullable=True),
        sa.Column("oculto", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("fixed_income_positions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_fixed_income_positions_user_id"), ["user_id"], unique=False
        )

    op.execute("DELETE FROM portfolio WHERE ticker LIKE 'RF!_%' ESCAPE '!'")


def downgrade() -> None:
    with op.batch_alter_table("fixed_income_positions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_fixed_income_positions_user_id"))

    op.drop_table("fixed_income_positions")
