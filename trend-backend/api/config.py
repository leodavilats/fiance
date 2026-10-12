from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


class ConfiguracaoAusente(RuntimeError):
    pass


def _obrigatoria(nome: str) -> str:
    valor = (os.environ.get(nome) or "").strip()
    if not valor:
        raise ConfiguracaoAusente(f"{nome} não está definida, e o painel não tem default para ela.")
    return valor


def _url_do_banco(url: str) -> str:
    for antigo in ("postgres://", "postgresql://"):
        if url.startswith(antigo):
            return "postgresql+psycopg://" + url[len(antigo) :]
    return url


@dataclass(frozen=True)
class Configuracao:
    database_url: str
    usuario: str
    senha: str
    docs: Path
    pesquisa: Path
    front: Path


def carregar() -> Configuracao:
    return Configuracao(
        database_url=_url_do_banco(_obrigatoria("DATABASE_URL")),
        usuario=_obrigatoria("TREND_USUARIO"),
        senha=_obrigatoria("TREND_SENHA"),
        docs=Path(os.environ.get("TREND_DOCS") or RAIZ / "docs"),
        pesquisa=Path(os.environ.get("TREND_PESQUISA") or RAIZ / "trend-backend"),
        front=Path(os.environ.get("TREND_FRONT") or RAIZ / "trend-frontend" / "dist"),
    )
