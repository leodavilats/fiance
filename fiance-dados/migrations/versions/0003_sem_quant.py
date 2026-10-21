from __future__ import annotations

from alembic import op

revision = "0003_sem_quant"
down_revision = "0002_planos_pagos"
branch_labels = None
depends_on = None

S = "acesso"


# A base não é entregue em arquivo, e o Quant saiu com a exportação (ADR-030). Conta que estiver
# nele vai para o Pro, que tem os mesmos recursos com limites menores.
def upgrade() -> None:
    op.execute(f"UPDATE {S}.conta SET plano = 'pro' WHERE plano = 'quant'")
    op.execute(f"UPDATE {S}.assinatura SET plano = 'pro' WHERE plano = 'quant'")
    op.execute(f"UPDATE {S}.plano SET recursos = array_remove(recursos, 'exportacao')")
    op.execute(f"DELETE FROM {S}.plano WHERE codigo = 'quant'")


def downgrade() -> None:
    op.execute(
        f"UPDATE {S}.plano SET recursos = array_append(recursos, 'exportacao') "
        "WHERE codigo IN ('interno', 'convidado')"
    )
    op.execute(
        f"""
        INSERT INTO {S}.plano (codigo, nome, descricao, limite_por_minuto, limite_por_dia,
            historico_dias, chaves_maximas, preco_mensal_centavos, preco_anual_centavos,
            recursos, ordem, publico)
        VALUES ('quant', 'Quant',
            'Tudo, com limites altos, exportação da base e uso comercial interno, sob contrato.',
            300, 300000, NULL, 20, 49000, NULL,
            ARRAY['serie', 'ponto_no_tempo', 'informes', 'exportacao']::text[], 3, true)
        """
    )
