from __future__ import annotations

from alembic import op

revision = "0018_ativo_hoje"
down_revision = "0017_fii_mensal_e_pagamento"
branch_labels = None
depends_on = None

# Uma linha por ticker negociado nos últimos 30 dias: o que o app lê. Só números brutos; os índices
# (P/L, P/VP, ROE, yield) são regra do backend. BDI 13 (Fiagro) fica de fora, como no produto.
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
    SELECT DISTINCT ON (cnpj) cnpj, acoes FROM (
        SELECT d.cnpj, d.data_referencia AS data,
            k.acoes_total - coalesce(k.tesouraria_total, 0) AS acoes
        FROM mercado.composicao_capital k JOIN mercado.documento d ON d.id = k.documento_id
        UNION ALL
        SELECT cnpj, data_aprovacao, acoes_total FROM mercado.capital_social
    ) x
    WHERE acoes > 0
    ORDER BY cnpj, data DESC
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
    m.cnpj, ac.acoes, fii.valor_patrimonial_cota, fii.referencia_cota,
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
    op.execute(_ATIVO_HOJE)
    op.execute("CREATE UNIQUE INDEX ix_ativo_hoje ON mercado.ativo_hoje (codigo)")
    op.execute("GRANT SELECT ON mercado.ativo_hoje TO mercado_leitura")
    op.create_index("ix_cotacao_codigo_data", "cotacao", ["codigo", "data"], schema="mercado")


def downgrade() -> None:
    op.drop_index("ix_cotacao_codigo_data", "cotacao", schema="mercado")
    op.execute("DROP MATERIALIZED VIEW mercado.ativo_hoje")
