from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0013_caixa_de_avisos"
down_revision = "0012_sugestao_seguida_do_razao"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inbox_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("dedup_key", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("ticker", sa.String(), nullable=True),
        sa.Column("action", sa.String(), nullable=True),
        sa.Column("action_label", sa.String(), nullable=True),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.Column("read_at", sa.Float(), nullable=True),
    )
    op.create_index("ix_inbox_items_user_id", "inbox_items", ["user_id"])
    op.create_index(
        "ux_inbox_items_user_dedup", "inbox_items", ["user_id", "dedup_key"], unique=True
    )
    op.create_index("ix_inbox_items_user_created", "inbox_items", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_inbox_items_user_created", table_name="inbox_items")
    op.drop_index("ux_inbox_items_user_dedup", table_name="inbox_items")
    op.drop_index("ix_inbox_items_user_id", table_name="inbox_items")
    op.drop_table("inbox_items")
