from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008_proventos_e_serie"
down_revision = "0007_papel_so_acao"
branch_labels = None
depends_on = None

S = "mercado"
_CLASSE = "substring(a.especie FROM '^(ON|PNA|PNB|PNC|PND|PNE|PNF|PN|UNT)')"

# Preço ajustado: divide-se pelo produto dos multiplicadores dos eventos com data-com igual ou
# posterior ao dia. Provento entra no primeiro pregão depois da data-com, na mesma escala do preço.
_SERIE = rf"""
CREATE MATERIALIZED VIEW mercado.serie_papel AS
WITH papel AS (
    SELECT DISTINCT ON (cnpj, classe, data) cnpj, classe, data, codigo, isin,
        fechamento / fator_cotacao AS fechamento, volume
    FROM mercado.cotacao_papel
    ORDER BY cnpj, classe, data, volume DESC
),
evento_papel AS (
    SELECT cnpj, classe, data_com, exp(sum(ln(multiplicador))) AS multiplicador
    FROM (
        SELECT DISTINCT m.cnpj, {_CLASSE} AS classe, e.data_com, e.tipo, e.multiplicador
        FROM mercado.evento e
        JOIN mercado.ativo a ON a.isin = e.isin
        JOIN mercado.emissor m ON m.codigo = substr(e.isin, 3, 4)
        WHERE e.status IN ('confirmado', 'sem_preco') AND e.multiplicador > 0
    ) x
    WHERE classe IS NOT NULL
    GROUP BY cnpj, classe, data_com
),
ajuste AS (
    SELECT cnpj, classe, data_com,
        lag(data_com) OVER (PARTITION BY cnpj, classe ORDER BY data_com) AS data_com_anterior,
        exp(sum(ln(multiplicador)) OVER (
            PARTITION BY cnpj, classe ORDER BY data_com DESC ROWS UNBOUNDED PRECEDING)) AS fator
    FROM evento_papel
),
provento_papel AS (
    SELECT m.cnpj, p.classe, p.data_com, sum(p.valor) AS valor
    FROM mercado.provento p
    JOIN mercado.emissor m ON m.codigo = p.emissor
    GROUP BY m.cnpj, p.classe, p.data_com
),
provento_ajustado AS (
    SELECT p.cnpj, p.classe, p.data_com, p.valor / coalesce(a.fator, 1) AS valor
    FROM provento_papel p
    LEFT JOIN ajuste a ON a.cnpj = p.cnpj AND a.classe = p.classe AND p.data_com <= a.data_com
        AND (a.data_com_anterior IS NULL OR p.data_com > a.data_com_anterior)
),
dia AS (
    SELECT p.*, lag(p.data) OVER (PARTITION BY p.cnpj, p.classe ORDER BY p.data) AS data_anterior,
        coalesce(a.fator, 1) AS fator_ajuste,
        p.fechamento / coalesce(a.fator, 1) AS fechamento_ajustado
    FROM papel p
    LEFT JOIN ajuste a ON a.cnpj = p.cnpj AND a.classe = p.classe AND p.data <= a.data_com
        AND (a.data_com_anterior IS NULL OR p.data > a.data_com_anterior)
),
provento_no_dia AS (
    SELECT d.cnpj, d.classe, d.data, sum(v.valor) AS provento
    FROM dia d
    JOIN provento_ajustado v ON v.cnpj = d.cnpj AND v.classe = d.classe
        AND v.data_com >= d.data_anterior AND v.data_com < d.data
    GROUP BY d.cnpj, d.classe, d.data
),
com_provento AS (
    SELECT d.*, coalesce(n.provento, 0) AS provento
    FROM dia d
    LEFT JOIN provento_no_dia n ON n.cnpj = d.cnpj AND n.classe = d.classe AND n.data = d.data
)
SELECT cnpj, classe, data, codigo, isin, fechamento, volume, fator_ajuste, fechamento_ajustado,
    provento,
    (fechamento_ajustado + provento)
        / lag(fechamento_ajustado) OVER (PARTITION BY cnpj, classe ORDER BY data) - 1
        AS retorno_total
FROM com_provento
WITH NO DATA
"""


def _coleta() -> sa.Column:
    return sa.Column("coleta_id", sa.BigInteger, sa.ForeignKey(f"{S}.coleta.id"), nullable=False)


def upgrade() -> None:
    op.create_table(
        "provento",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("emissor", sa.Text, nullable=False),
        sa.Column("classe", sa.Text, nullable=False),
        sa.Column("data_com", sa.Date, nullable=False),
        sa.Column("tipo", sa.Text, nullable=False),
        sa.Column("valor", sa.Numeric, nullable=False),
        sa.Column("data_aprovacao", sa.Date),
        sa.Column("preco_vespera", sa.Numeric),
        _coleta(),
        schema=S,
    )
    op.create_index("ix_provento_emissor", "provento", ["emissor", "classe", "data_com"], schema=S)

    op.create_table(
        "evento",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("emissor", sa.Text, nullable=False),
        sa.Column("isin", sa.Text, nullable=False),
        sa.Column("data_com", sa.Date, nullable=False),
        sa.Column("tipo", sa.Text, nullable=False),
        sa.Column("fator", sa.Numeric, nullable=False),
        sa.Column("multiplicador", sa.Numeric),
        sa.Column("data_aprovacao", sa.Date),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("razao_observada", sa.Numeric),
        _coleta(),
        sa.CheckConstraint(
            "status IN ('confirmado', 'divergente', 'sem_preco', 'nao_ajusta')",
            name="ck_evento_status",
        ),
        schema=S,
    )
    op.create_index("ix_evento_emissor", "evento", ["emissor"], schema=S)

    op.execute(_SERIE)
    op.execute("CREATE UNIQUE INDEX ix_serie_papel ON mercado.serie_papel (cnpj, classe, data)")
    op.execute("GRANT SELECT ON mercado.serie_papel TO mercado_leitura")


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW mercado.serie_papel")
    op.drop_table("evento", schema=S)
    op.drop_table("provento", schema=S)
