from __future__ import annotations

from alembic import op

revision = "0007_papel_so_acao"
down_revision = "0006_cotacao_papel"
branch_labels = None
depends_on = None

_CLASSE = "substring(a.especie FROM '^(ON|PNA|PNB|PNC|PND|PNE|PNF|PN|UNT)')"

# Recibo e direito de subscrição (ITSA9, BBDC10) têm espécie ON ou PN, mas código BDI 10: entravam na
# série do papel como uma segunda cotação do mesmo dia.
_VISAO = rf"""
CREATE OR REPLACE VIEW mercado.cotacao_papel AS
SELECT m.cnpj, {_CLASSE} AS classe,
    c.data, c.isin, c.codigo, c.abertura, c.maxima, c.minima, c.media, c.fechamento,
    c.negocios, c.quantidade, c.volume, c.fator_cotacao
FROM mercado.cotacao c
JOIN mercado.ativo a ON a.isin = c.isin
JOIN mercado.emissor m ON m.codigo = substr(c.isin, 3, 4)
WHERE {_CLASSE} IS NOT NULL AND c.codbdi IN ('02', '05', '06', '07', '08')
"""

_ANTERIOR = rf"""
CREATE OR REPLACE VIEW mercado.cotacao_papel AS
SELECT m.cnpj, {_CLASSE} AS classe,
    c.data, c.isin, c.codigo, c.abertura, c.maxima, c.minima, c.media, c.fechamento,
    c.negocios, c.quantidade, c.volume, c.fator_cotacao
FROM mercado.cotacao c
JOIN mercado.ativo a ON a.isin = c.isin
JOIN mercado.emissor m ON m.codigo = substr(c.isin, 3, 4)
WHERE {_CLASSE} IS NOT NULL
"""


def upgrade() -> None:
    op.execute(_VISAO)


def downgrade() -> None:
    op.execute(_ANTERIOR)
