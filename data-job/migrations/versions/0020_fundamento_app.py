from __future__ import annotations

from alembic import op

revision = "0020_fundamento_app"
down_revision = "0019_acoes_pelo_fre"
branch_labels = None
depends_on = None

# As visões de fundamento recalculam as linhas da demonstração a cada consulta: ~3 s por empresa.
# O app lê esta, recalculada uma vez por rodada. Só o período do próprio documento — o comparativo
# do ano anterior já está no documento daquele ano.
_FUNDAMENTO_APP = """
CREATE MATERIALIZED VIEW mercado.fundamento_app AS
SELECT r.cnpj, r.tipo, r.data_referencia, r.versao, r.fim_exercicio, r.receita,
    r.lucro_controladores, b.patrimonio_controladores, b.divida_bruta
FROM mercado.fundamento_resultado r
LEFT JOIN mercado.fundamento_balanco b
    ON b.documento_id = r.documento_id AND b.data = r.data_referencia
WHERE r.fim_exercicio = r.data_referencia
  AND r.inicio_exercicio = make_date(extract(year FROM r.fim_exercicio)::int, 1, 1)
WITH NO DATA
"""


def upgrade() -> None:
    op.execute(_FUNDAMENTO_APP)
    op.execute(
        "CREATE UNIQUE INDEX ix_fundamento_app "
        "ON mercado.fundamento_app (cnpj, tipo, data_referencia, versao)"
    )
    op.execute("GRANT SELECT ON mercado.fundamento_app TO mercado_leitura")


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW mercado.fundamento_app")
