from __future__ import annotations

from dataclasses import dataclass

import sqlalchemy as sa

PAPEL_DE_LEITURA = "mercado_leitura"


@dataclass(frozen=True)
class Bancos:
    leitura: sa.Engine
    acesso: sa.Engine


def criar(url: str) -> Bancos:
    leitura = sa.create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5)

    @sa.event.listens_for(leitura, "connect")
    def _so_leitura(conexao, _registro) -> None:
        # O dado de mercado é lido com o papel que só lê: a API não escreve em `mercado`.
        with conexao.cursor() as cursor:
            cursor.execute(f"SET ROLE {PAPEL_DE_LEITURA}")
            cursor.execute("SET default_transaction_read_only = on")
        conexao.commit()

    acesso = sa.create_engine(url, pool_pre_ping=True, pool_size=3, max_overflow=2)
    return Bancos(leitura=leitura, acesso=acesso)
