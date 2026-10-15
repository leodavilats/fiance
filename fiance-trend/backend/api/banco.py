from __future__ import annotations

import sqlalchemy as sa

PAPEL_DE_LEITURA = "mercado_leitura"


def criar(url: str) -> sa.Engine:
    engine = sa.create_engine(url, pool_pre_ping=True, pool_size=3, max_overflow=2)

    @sa.event.listens_for(engine, "connect")
    def _so_leitura(conexao, _registro) -> None:
        # O painel usa a conexão que o Railway já dá e assume o papel que só lê: nenhuma senha nova.
        with conexao.cursor() as cursor:
            cursor.execute(f"SET ROLE {PAPEL_DE_LEITURA}")
            cursor.execute("SET default_transaction_read_only = on")
        conexao.commit()

    return engine
