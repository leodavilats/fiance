from __future__ import annotations

from alembic import op

revision = "0005_fundamento"
down_revision = "0004_indicador_e_leitura"
branch_labels = None
depends_on = None

# A conta muda de código conforme o plano da empresa (o lucro dos controladores é 3.11.01 na
# Petrobras e 3.09.01 no Itaú); a descrição das contas fixas da CVM é estável, e as variações abaixo
# foram medidas sobre todos os documentos carregados em 2026-10-10.
_RESULTADO = r"""
CREATE VIEW mercado.fundamento_resultado AS
WITH contas AS (
    SELECT l.documento_id, l.inicio_exercicio, l.fim_exercicio, bool_or(l.consolidado) AS consolidado,
        max(l.valor) FILTER (WHERE l.conta ~ '^3\.[0-9]{2}$' AND lower(l.descricao) IN (
            'receita de venda de bens e/ou serviços', 'receitas da intermediação financeira',
            'receitas de intermediação financeira', 'receitas das operações')) AS receita,
        max(l.valor) FILTER (WHERE l.conta ~ '^3\.[0-9]{2}$' AND lower(l.descricao) =
            'resultado antes do resultado financeiro e dos tributos') AS ebit,
        max(l.valor) FILTER (WHERE l.conta ~ '^3\.[0-9]{2}$' AND lower(l.descricao) IN (
            'resultado antes dos tributos sobre o lucro', 'resultado antes tributação/participações'
        )) AS lucro_antes_ir,
        max(l.valor) FILTER (WHERE l.conta ~ '^3\.[0-9]{2}$' AND lower(l.descricao) IN (
            'lucro/prejuízo consolidado do período', 'lucro/prejuízo do período',
            'lucro ou prejuízo líquido do período', 'lucro ou prejuízo líquido consolidado do período'
        )) AS lucro_liquido,
        max(l.valor) FILTER (WHERE l.conta ~ '^3\.[0-9]{2}\.[0-9]{2}$' AND lower(l.descricao) IN (
            'atribuído a sócios da empresa controladora', 'atribuído aos sócios da empresa controladora'
        )) AS lucro_atribuido
    FROM mercado.demonstracao_linha l
    WHERE l.demonstracao = 'DRE'
    GROUP BY l.documento_id, l.inicio_exercicio, l.fim_exercicio
)
SELECT d.id AS documento_id, d.cnpj, d.tipo, d.data_referencia, d.versao, d.data_entrega,
    c.inicio_exercicio, c.fim_exercicio, c.consolidado,
    c.receita, c.ebit, c.lucro_antes_ir, c.lucro_liquido,
    coalesce(c.lucro_atribuido, CASE WHEN NOT c.consolidado THEN c.lucro_liquido END)
        AS lucro_controladores
FROM contas c
JOIN mercado.documento d ON d.id = c.documento_id
"""

_BALANCO = r"""
CREATE VIEW mercado.fundamento_balanco AS
WITH contas AS (
    SELECT l.documento_id, l.fim_exercicio AS data, bool_or(l.consolidado) AS consolidado,
        max(l.valor) FILTER (WHERE l.demonstracao = 'BPA' AND l.conta = '1') AS ativo_total,
        max(l.valor) FILTER (WHERE l.demonstracao = 'BPA'
            AND l.conta ~ '^1\.[0-9]{2}(\.[0-9]{2})?$'
            AND lower(l.descricao) = 'caixa e equivalentes de caixa') AS caixa,
        sum(l.valor) FILTER (WHERE l.demonstracao = 'BPP' AND l.conta ~ '^2\.0[12]\.[0-9]{2}$'
            AND lower(l.descricao) = 'empréstimos e financiamentos') AS divida_bruta,
        max(l.valor) FILTER (WHERE l.demonstracao = 'BPP' AND l.conta ~ '^2\.[0-9]{2}$'
            AND lower(l.descricao) IN ('patrimônio líquido consolidado', 'patrimônio líquido'))
            AS patrimonio_liquido,
        max(l.valor) FILTER (WHERE l.demonstracao = 'BPP' AND l.conta ~ '^2\.[0-9]{2}\.[0-9]{2}$'
            AND lower(l.descricao) IN ('participação dos acionistas não controladores',
                'patrimônio líquido atribuído aos não controladores')) AS nao_controladores
    FROM mercado.demonstracao_linha l
    WHERE l.demonstracao IN ('BPA', 'BPP')
    GROUP BY l.documento_id, l.fim_exercicio
)
SELECT d.id AS documento_id, d.cnpj, d.tipo, d.data_referencia, d.versao, d.data_entrega,
    c.data, c.consolidado, c.ativo_total, c.caixa, c.divida_bruta, c.patrimonio_liquido,
    c.patrimonio_liquido - coalesce(c.nao_controladores, 0) AS patrimonio_controladores
FROM contas c
JOIN mercado.documento d ON d.id = c.documento_id
"""


def upgrade() -> None:
    op.execute(_RESULTADO)
    op.execute(_BALANCO)


def downgrade() -> None:
    op.execute("DROP VIEW mercado.fundamento_balanco")
    op.execute("DROP VIEW mercado.fundamento_resultado")
