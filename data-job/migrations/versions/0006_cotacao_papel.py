from __future__ import annotations

from alembic import op

revision = "0006_cotacao_papel"
down_revision = "0005_fundamento"
branch_labels = None
depends_on = None

# A troca de ticker cria ISIN novo (VVAR3, VIIA3 e BHIA3 são três ISINs da mesma empresa); a série
# contínua de um papel é a empresa mais a classe da ação.
_VISAO = r"""
CREATE VIEW mercado.cotacao_papel AS
SELECT m.cnpj,
    substring(a.especie FROM '^(ON|PNA|PNB|PNC|PND|PNE|PNF|PN|UNT)') AS classe,
    c.data, c.isin, c.codigo, c.abertura, c.maxima, c.minima, c.media, c.fechamento,
    c.negocios, c.quantidade, c.volume, c.fator_cotacao
FROM mercado.cotacao c
JOIN mercado.ativo a ON a.isin = c.isin
JOIN mercado.emissor m ON m.codigo = substr(c.isin, 3, 4)
WHERE substring(a.especie FROM '^(ON|PNA|PNB|PNC|PND|PNE|PNF|PN|UNT)') IS NOT NULL
"""


def upgrade() -> None:
    op.execute(_VISAO)


def downgrade() -> None:
    op.execute("DROP VIEW mercado.cotacao_papel")
