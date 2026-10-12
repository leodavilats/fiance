from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012_serie_fundo"
down_revision = "0011_capital_social"
branch_labels = None
depends_on = None

_CLASSE = "substring(a.especie FROM '^(CI|DRN|DRE|DR1|DR2|DR3)')"

# FII (BDI 12), fundo listado — ETF, Fiagro, FI-Infra — (BDI 14) e BDR (BDI 34 a 36). Não há CNPJ de
# companhia: a cota é o código do emissor no ISIN mais a classe. As regras são as de serie_papel.
_SERIE = rf"""
CREATE MATERIALIZED VIEW mercado.serie_fundo AS
WITH cota AS (
    SELECT substr(c.isin, 3, 4) AS emissor, {_CLASSE} AS classe,
        CASE WHEN c.codbdi = '12' THEN 'fii' WHEN c.codbdi = '14' THEN 'fundo' ELSE 'bdr' END
            AS tipo_ativo,
        c.data, c.codigo, c.isin, c.fechamento / c.fator_cotacao AS fechamento, c.volume
    FROM mercado.cotacao c
    JOIN mercado.ativo a ON a.isin = c.isin
    WHERE c.codbdi IN ('12', '14', '34', '35', '36') AND {_CLASSE} IS NOT NULL
),
papel AS (
    SELECT DISTINCT ON (emissor, classe, data) * FROM cota
    ORDER BY emissor, classe, data, volume DESC
),
evento_ativo AS (
    SELECT DISTINCT e.emissor, {_CLASSE} AS classe, e.data_com, e.tipo, e.multiplicador, e.status
    FROM mercado.evento e
    JOIN mercado.ativo a ON a.isin = e.isin
),
evento_papel AS (
    SELECT emissor, classe, data_com, exp(sum(ln(multiplicador))) AS multiplicador
    FROM (
        SELECT DISTINCT emissor, classe, data_com, tipo, multiplicador FROM evento_ativo
        WHERE classe IS NOT NULL AND status IN ('confirmado', 'sem_preco') AND multiplicador > 0
    ) x
    GROUP BY emissor, classe, data_com
),
ajuste AS (
    SELECT emissor, classe, data_com,
        lag(data_com) OVER (PARTITION BY emissor, classe ORDER BY data_com) AS data_com_anterior,
        exp(sum(ln(multiplicador)) OVER (
            PARTITION BY emissor, classe ORDER BY data_com DESC ROWS UNBOUNDED PRECEDING)) AS fator
    FROM evento_papel
),
provento_papel AS (
    SELECT emissor, classe, data_com, sum(valor) AS valor
    FROM mercado.provento GROUP BY emissor, classe, data_com
),
provento_ajustado AS (
    SELECT p.emissor, p.classe, p.data_com, p.valor / coalesce(a.fator, 1) AS valor
    FROM provento_papel p
    LEFT JOIN ajuste a ON a.emissor = p.emissor AND a.classe = p.classe AND p.data_com <= a.data_com
        AND (a.data_com_anterior IS NULL OR p.data_com > a.data_com_anterior)
),
dia AS (
    SELECT p.*, lag(p.data) OVER (PARTITION BY p.emissor, p.classe ORDER BY p.data) AS data_anterior,
        coalesce(a.fator, 1) AS fator_ajuste, p.fechamento / coalesce(a.fator, 1) AS fechamento_ajustado
    FROM papel p
    LEFT JOIN ajuste a ON a.emissor = p.emissor AND a.classe = p.classe AND p.data <= a.data_com
        AND (a.data_com_anterior IS NULL OR p.data > a.data_com_anterior)
),
provento_no_dia AS (
    SELECT d.emissor, d.classe, d.data, sum(v.valor) AS provento
    FROM dia d
    JOIN provento_ajustado v ON v.emissor = d.emissor AND v.classe = d.classe
        AND v.data_com >= d.data_anterior AND v.data_com < d.data
    GROUP BY d.emissor, d.classe, d.data
),
evento_no_dia AS (
    SELECT DISTINCT d.emissor, d.classe, d.data
    FROM dia d
    JOIN (SELECT DISTINCT emissor, data_com FROM evento_ativo) e ON e.emissor = d.emissor
        AND e.data_com >= d.data_anterior AND e.data_com < d.data
),
completo AS (
    SELECT d.*, coalesce(n.provento, 0) AS provento, x.data IS NOT NULL AS evento_no_intervalo,
        (d.fechamento_ajustado + coalesce(n.provento, 0))
            / lag(d.fechamento_ajustado) OVER (PARTITION BY d.emissor, d.classe ORDER BY d.data) - 1
            AS retorno_total
    FROM dia d
    LEFT JOIN provento_no_dia n ON n.emissor = d.emissor AND n.classe = d.classe AND n.data = d.data
    LEFT JOIN evento_no_dia x ON x.emissor = d.emissor AND x.classe = d.classe AND x.data = d.data
)
SELECT emissor, classe, tipo_ativo, data, codigo, isin, fechamento, volume, fator_ajuste,
    fechamento_ajustado, provento, retorno_total, data - data_anterior AS dias_desde_anterior,
    abs(retorno_total) > 0.5 AND NOT evento_no_intervalo AS salto_sem_evento
FROM completo
WITH NO DATA
"""


def upgrade() -> None:
    op.add_column(
        "provento",
        sa.Column("origem", sa.Text, nullable=False, server_default="b3_historico"),
        schema="mercado",
    )
    op.execute(_SERIE)
    op.execute("CREATE UNIQUE INDEX ix_serie_fundo ON mercado.serie_fundo (emissor, classe, data)")
    op.execute("GRANT SELECT ON mercado.serie_fundo TO mercado_leitura")


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW mercado.serie_fundo")
    op.drop_column("provento", "origem", schema="mercado")
