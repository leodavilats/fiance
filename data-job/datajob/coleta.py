from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import sqlalchemy as sa

from datajob import armazenamento
from datajob.esquema import coleta

Processar = Callable[[sa.Connection, bytes, int], tuple[int, int, int]]


@dataclass(frozen=True)
class Resultado:
    coleta_id: int
    status: str
    lidas: int = 0
    gravadas: int = 0
    quarentena: int = 0


def _agora() -> datetime:
    return datetime.now(UTC)


def _ja_coletado(engine: sa.Engine, fonte: str, hash_: str) -> bool:
    with engine.connect() as conn:
        consulta = sa.select(sa.literal(True)).where(
            coleta.c.fonte == fonte, coleta.c.hash == hash_, coleta.c.status == "ok"
        )
        return conn.execute(consulta.limit(1)).first() is not None


def _abrir(engine: sa.Engine, fonte: str, arquivo: str, hash_: str, status: str) -> int:
    with engine.begin() as conn:
        return conn.execute(
            sa.insert(coleta)
            .values(fonte=fonte, arquivo=arquivo, hash=hash_, status=status, iniciada_em=_agora())
            .returning(coleta.c.id)
        ).scalar_one()


def _fechar(engine: sa.Engine, coleta_id: int, **campos) -> None:
    with engine.begin() as conn:
        conn.execute(
            sa.update(coleta)
            .where(coleta.c.id == coleta_id)
            .values(terminada_em=_agora(), **campos)
        )


def executar(
    engine: sa.Engine,
    raiz: Path,
    fonte: str,
    arquivo: str,
    conteudo: bytes,
    processar: Processar,
    forcar: bool = False,
) -> Resultado:
    hash_ = armazenamento.hash_de(conteudo)
    armazenamento.guardar(raiz, fonte, arquivo, conteudo)

    if not forcar and _ja_coletado(engine, fonte, hash_):
        coleta_id = _abrir(engine, fonte, arquivo, hash_, "pulada")
        _fechar(engine, coleta_id)
        return Resultado(coleta_id, "pulada")

    coleta_id = _abrir(engine, fonte, arquivo, hash_, "rodando")
    try:
        with engine.begin() as conn:
            lidas, gravadas, quarentena = processar(conn, conteudo, coleta_id)
    except Exception as e:
        _fechar(engine, coleta_id, status="falhou", erro=f"{type(e).__name__}: {e}")
        raise

    _fechar(
        engine,
        coleta_id,
        status="ok",
        linhas_lidas=lidas,
        linhas_gravadas=gravadas,
        linhas_quarentena=quarentena,
    )
    return Resultado(coleta_id, "ok", lidas, gravadas, quarentena)
