from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfiguracaoAusente(RuntimeError):
    pass


def url_do_banco(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def _obrigatoria(nome: str) -> str:
    valor = (os.environ.get(nome) or "").strip()
    if not valor:
        raise ConfiguracaoAusente(
            f"{nome} não está definida, e o data-job não tem default para ela."
        )
    return valor


@dataclass(frozen=True)
class Configuracao:
    database_url: str
    bruto_dir: Path


def carregar() -> Configuracao:
    return Configuracao(
        database_url=url_do_banco(_obrigatoria("DATABASE_URL")),
        bruto_dir=Path(_obrigatoria("DATAJOB_BRUTO_DIR")),
    )
