from __future__ import annotations

from alembic import op

revision = "0009_serie_marca_saltos"
down_revision = "0008_proventos_e_serie"
branch_labels = None
depends_on = None

_CLASSE = "substring(a.especie FROM '^(ON|PNA|PNB|PNC|PND|PNE|PNF|PN|UNT)')"

# A lista de eventos da B3 não é completa (CASH3 em 2021, KEPL3 e GFSA3 em 2022 faltam): a série marca
# o salto que nenhum evento explica, em vez de escondê-lo.
_SERIE = rf"""
CREATE MATERIALIZED VIEW mercado.serie_papel AS
WITH papel AS (
    SELECT DISTINCT ON (cnpj, classe, data) cnpj, classe, data, codigo, isin,
        fechamento / fator_cotacao AS fechamento, volume
    FROM mercado.cotacao_papel
    ORDER BY cnpj, classe, data, volume DESC
),
evento_ativo AS (
    SELECT DISTINCT m.cnpj, {_CLASSE} AS classe, e.data_com, e.tipo, e.multiplicador, e.status
    FROM mercado.evento e
    JOIN mercado.ativo a ON a.isin = e.isin
    JOIN mercado.emissor m ON m.codigo = substr(e.isin, 3, 4)
),
evento_papel AS (
    SELECT cnpj, classe, data_com, exp(sum(ln(multiplicador))) AS multiplicador
    FROM evento_ativo
    WHERE classe IS NOT NULL AND status IN ('confirmado', 'sem_preco') AND multiplicador > 0
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
evento_no_dia AS (
    SELECT DISTINCT d.cnpj, d.classe, d.data
    FROM dia d
    JOIN (SELECT DISTINCT cnpj, data_com FROM evento_ativo) e ON e.cnpj = d.cnpj
        AND e.data_com >= d.data_anterior AND e.data_com < d.data
),
completo AS (
    SELECT d.*, coalesce(n.provento, 0) AS provento, x.data IS NOT NULL AS evento_no_intervalo,
        (d.fechamento_ajustado + coalesce(n.provento, 0))
            / lag(d.fechamento_ajustado) OVER (PARTITION BY d.cnpj, d.classe ORDER BY d.data) - 1
            AS retorno_total
    FROM dia d
    LEFT JOIN provento_no_dia n ON n.cnpj = d.cnpj AND n.classe = d.classe AND n.data = d.data
    LEFT JOIN evento_no_dia x ON x.cnpj = d.cnpj AND x.classe = d.classe AND x.data = d.data
)
SELECT cnpj, classe, data, codigo, isin, fechamento, volume, fator_ajuste, fechamento_ajustado,
    provento, retorno_total, data - data_anterior AS dias_desde_anterior,
    abs(retorno_total) > 0.5 AND NOT evento_no_intervalo AS salto_sem_evento
FROM completo
WITH NO DATA
"""


def upgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW mercado.serie_papel")
    op.execute(_SERIE)
    op.execute("CREATE UNIQUE INDEX ix_serie_papel ON mercado.serie_papel (cnpj, classe, data)")
    op.execute("GRANT SELECT ON mercado.serie_papel TO mercado_leitura")


def downgrade() -> None:
    raise NotImplementedError("A 0008 tem a série sem as marcas; recrie a partir dela.")
