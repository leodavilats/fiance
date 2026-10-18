from __future__ import annotations

from alembic import op

revision = "0022_confirmacao_pelo_tamanho"
down_revision = "0021_salto_perto_de_fator"
branch_labels = None
depends_on = None

# A regra de datajob/fontes/b3_proventos.py:confere, aplicada de uma vez ao que já está gravado; a
# coleta de cada emissor reaplica a mesma regra dali em diante (ADR-026).
_RECONFERIR = """
WITH tipo AS (
    SELECT DISTINCT ON (isin, data_com, tipo) isin, data_com, multiplicador, razao_observada
    FROM mercado.evento
    WHERE multiplicador > 0 AND razao_observada > 0 AND status IN ('confirmado', 'divergente')
    ORDER BY isin, data_com, tipo
),
grupo AS (
    SELECT isin, data_com, exp(sum(ln(multiplicador))) AS fator, max(razao_observada) AS observada
    FROM tipo GROUP BY isin, data_com
),
novo AS (
    SELECT isin, data_com,
        CASE
            WHEN abs(ln(fator)) <= ln(1.25) THEN abs(ln(observada / fator)) <= ln(1.25)
            ELSE abs(ln(observada / fator)) <= abs(ln(fator)) / 2
        END AS confere
    FROM grupo
)
UPDATE mercado.evento e
SET status = CASE WHEN n.confere THEN 'confirmado' ELSE 'divergente' END
FROM novo n
WHERE e.isin = n.isin AND e.data_com = n.data_com AND e.multiplicador IS NOT NULL
  AND e.status IN ('confirmado', 'divergente')
"""


def upgrade() -> None:
    op.execute(_RECONFERIR)
    op.execute("REFRESH MATERIALIZED VIEW mercado.serie_papel")
    op.execute("REFRESH MATERIALIZED VIEW mercado.serie_fundo")


def downgrade() -> None:
    raise NotImplementedError("a folga fixa de 12% recusava grupamento que aconteceu")
