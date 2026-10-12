from __future__ import annotations

from alembic import op

revision = "0019_acoes_pelo_fre"
down_revision = "0018_ativo_hoje"
branch_labels = None
depends_on = None

# O FRE dá a quantidade de ações em unidades; a composição do ITR, em algumas empresas, em milhares.
# Prefere-se o FRE, e a composição só entra na falta dele.
_ATIVO_HOJE = r"""
CREATE MATERIALIZED VIEW mercado.ativo_hoje AS
WITH dia AS (SELECT max(data) AS ultimo FROM mercado.cotacao),
recente AS (
    SELECT c.codigo, c.isin, c.data, c.fechamento / c.fator_cotacao AS fechamento,
        c.maxima / c.fator_cotacao AS maxima, c.minima / c.fator_cotacao AS minima, c.volume,
        row_number() OVER (PARTITION BY c.codigo ORDER BY c.data DESC) AS n
    FROM mercado.cotacao c, dia
    WHERE c.data > dia.ultimo - 366 AND c.codbdi IN ('02', '12', '14', '34', '35', '36')
),
faixa AS (
    SELECT codigo, max(maxima) AS maxima_52s, min(minima) AS minima_52s,
        avg(volume) FILTER (WHERE n <= 63) AS volume_medio
    FROM recente GROUP BY codigo
),
papel AS (
    SELECT r.codigo, r.isin, r.data, r.fechamento AS preco, a.nome_resumido,
        substr(r.isin, 3, 4) AS emissor,
        substring(a.especie FROM '^([A-Z0-9]+)') AS classe,
        CASE
            WHEN a.especie ~ '^DR' THEN 'bdr'
            WHEN a.especie ~ '^CI' AND a.codbdi IN ('02', '12') THEN 'fii'
            WHEN a.especie ~ '^CI' THEN 'etf'
            WHEN a.especie ~ '^(ON|PN|UNT)' THEN 'stock'
        END AS tipo
    FROM recente r
    JOIN mercado.ativo a ON a.isin = r.isin
    WHERE r.n = 1 AND r.data >= (SELECT ultimo FROM dia) - 30
),
acoes AS (
    SELECT DISTINCT ON (cnpj) cnpj, ordinarias, preferenciais FROM (
        SELECT cnpj, 1 AS preferencia, data_aprovacao AS data, data_referencia,
            acoes_ordinarias AS ordinarias, acoes_preferenciais AS preferenciais, acoes_total
        FROM mercado.capital_social
        UNION ALL
        SELECT d.cnpj, 2, d.data_referencia, d.data_referencia, k.acoes_ordinarias,
            k.acoes_preferenciais, k.acoes_total
        FROM mercado.composicao_capital k JOIN mercado.documento d ON d.id = k.documento_id
    ) x
    WHERE acoes_total > 0
    ORDER BY cnpj, preferencia, data DESC, data_referencia DESC
),
fii AS (
    SELECT DISTINCT ON (emissor) emissor, nome, segmento, valor_patrimonial_cota,
        referencia AS referencia_cota
    FROM mercado.fii_mensal ORDER BY emissor, referencia DESC
)
SELECT p.codigo, p.isin, p.tipo, p.emissor, p.classe, p.data, p.preco,
    (SELECT r.fechamento FROM recente r WHERE r.codigo = p.codigo AND r.n = 2) AS preco_anterior,
    f.maxima_52s, f.minima_52s, f.volume_medio,
    coalesce(e.nome_comercial, e.razao_social, fii.nome, p.nome_resumido) AS nome,
    coalesce(e.setor, fii.segmento) AS setor,
    m.cnpj, ac.ordinarias AS acoes_ordinarias, ac.preferenciais AS acoes_preferenciais,
    fii.valor_patrimonial_cota, fii.referencia_cota,
    (SELECT sum(v.valor) FROM mercado.provento v
        WHERE v.emissor = p.emissor AND v.classe = p.classe AND v.origem <> 'cvm_estimado'
          AND coalesce(v.data_pagamento, v.data_com) > p.data - 365
          AND coalesce(v.data_pagamento, v.data_com) <= p.data) AS proventos_12m
FROM papel p
JOIN faixa f ON f.codigo = p.codigo
LEFT JOIN mercado.emissor m ON m.codigo = p.emissor AND p.tipo = 'stock'
LEFT JOIN mercado.empresa e ON e.cnpj = m.cnpj
LEFT JOIN acoes ac ON ac.cnpj = m.cnpj
LEFT JOIN fii ON fii.emissor = p.emissor AND p.tipo = 'fii'
WHERE p.tipo IS NOT NULL
WITH NO DATA
"""


def upgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW mercado.ativo_hoje")
    op.execute(_ATIVO_HOJE)
    op.execute("CREATE UNIQUE INDEX ix_ativo_hoje ON mercado.ativo_hoje (codigo)")
    op.execute("GRANT SELECT ON mercado.ativo_hoje TO mercado_leitura")


def downgrade() -> None:
    raise NotImplementedError("a visão anterior misturava quantidades em unidades e em milhares")
