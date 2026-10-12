from __future__ import annotations

import threading
from datetime import date, timedelta
from decimal import Decimal

import sqlalchemy as sa

from app.core.config import get_settings

PAPEL_DE_LEITURA = "mercado_leitura"


class SemBaseDeMercado(RuntimeError):
    pass


_engine: sa.Engine | None = None
_engine_lock = threading.Lock()


def _url(bruta: str) -> str:
    for antigo in ("postgres://", "postgresql://"):
        if bruta.startswith(antigo):
            return "postgresql+psycopg://" + bruta[len(antigo) :]
    return bruta


def engine() -> sa.Engine:
    global _engine
    if _engine is not None:
        return _engine
    with _engine_lock:
        if _engine is None:
            url = get_settings().mercado_database_url.strip()
            if not url:
                raise SemBaseDeMercado("MERCADO_DATABASE_URL não está definida.")
            novo = sa.create_engine(_url(url), pool_pre_ping=True, pool_size=5, max_overflow=5)

            @sa.event.listens_for(novo, "connect")
            def _so_leitura(conexao, _registro) -> None:
                # A conexão que o Railway dá assume o papel que só lê: nenhuma senha nova.
                with conexao.cursor() as cursor:
                    cursor.execute(f"SET ROLE {PAPEL_DE_LEITURA}")
                    cursor.execute("SET default_transaction_read_only = on")
                conexao.commit()

            _engine = novo
    return _engine


def _simples(valor):
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, date):
        return valor.isoformat()
    return valor


def _linhas(conn: sa.Connection, sql: str, **parametros) -> list[dict]:
    return [
        {k: _simples(v) for k, v in r._mapping.items()}
        for r in conn.execute(sa.text(sql), parametros)
    ]


_ATIVOS = """
SELECT codigo, tipo, emissor, classe, data, preco, preco_anterior, maxima_52s, minima_52s,
    volume_medio, nome, setor, cnpj, acoes_ordinarias, acoes_preferenciais,
    valor_patrimonial_cota, referencia_cota, proventos_12m
FROM mercado.ativo_hoje
"""

_DOCUMENTOS = "SELECT id FROM mercado.documento WHERE cnpj = :cnpj"

_RESULTADOS = """
SELECT tipo, data_referencia, versao, fim_exercicio, receita, lucro_controladores
FROM mercado.fundamento_resultado
WHERE documento_id = ANY(:documentos)
  AND inicio_exercicio = make_date(extract(year FROM fim_exercicio)::int, 1, 1)
"""

_BALANCOS = """
SELECT tipo, data_referencia, versao, patrimonio_controladores, divida_bruta
FROM mercado.fundamento_balanco
WHERE documento_id = ANY(:documentos) AND data = data_referencia
"""


def _pacotes(conn: sa.Connection, ativos: list[dict]) -> dict[str, dict]:
    pacotes = {}
    for ativo in ativos:
        pacote = {"ativo": ativo, "irmaos": [], "resultados": [], "balancos": []}
        if ativo["tipo"] == "stock" and ativo["cnpj"]:
            pacote["irmaos"] = _linhas(
                conn,
                "SELECT codigo, classe, preco, volume_medio FROM mercado.ativo_hoje "
                "WHERE cnpj = :cnpj",
                cnpj=ativo["cnpj"],
            )
            documentos = list(conn.execute(sa.text(_DOCUMENTOS), {"cnpj": ativo["cnpj"]}).scalars())
            if documentos:
                pacote["resultados"] = _linhas(conn, _RESULTADOS, documentos=documentos)
                pacote["balancos"] = _linhas(conn, _BALANCOS, documentos=documentos)
        pacotes[ativo["codigo"]] = pacote
    return pacotes


def ler_pacotes(codigos: list[str]) -> dict[str, dict]:
    with engine().connect() as conn:
        ativos = _linhas(conn, _ATIVOS + " WHERE codigo = ANY(:codigos)", codigos=codigos)
        return _pacotes(conn, ativos)


def ler_lista() -> list[dict]:
    with engine().connect() as conn:
        return _linhas(
            conn, "SELECT codigo, tipo, nome, setor, volume_medio FROM mercado.ativo_hoje"
        )


def ler_historico(codigo: str, dias: int) -> dict[str, float]:
    with engine().connect() as conn:
        ultimo = conn.execute(
            sa.text("SELECT max(data) FROM mercado.cotacao WHERE codigo = :c"), {"c": codigo}
        ).scalar()
        if ultimo is None:
            return {}
        linhas = conn.execute(
            sa.text(
                "SELECT data, fechamento / fator_cotacao AS preco FROM mercado.cotacao "
                "WHERE codigo = :c AND data > :desde ORDER BY data"
            ),
            {"c": codigo, "desde": ultimo - timedelta(days=dias)},
        )
        return {r.data.isoformat(): float(r.preco) for r in linhas}


def ler_proventos(codigo: str) -> list[dict]:
    with engine().connect() as conn:
        ativo = conn.execute(
            sa.text("SELECT emissor, classe FROM mercado.ativo_hoje WHERE codigo = :c"),
            {"c": codigo},
        ).first()
        if ativo is None:
            return []
        return _linhas(
            conn,
            """
            SELECT data_com, data_pagamento, valor FROM mercado.provento
            WHERE emissor = :emissor AND classe = :classe AND origem <> 'cvm_estimado'
            ORDER BY data_com
            """,
            emissor=ativo.emissor,
            classe=ativo.classe,
        )
