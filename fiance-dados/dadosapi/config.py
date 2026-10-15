from __future__ import annotations

import os
from dataclasses import dataclass

TAMANHO_MINIMO_DO_TOKEN = 32


class ConfiguracaoAusente(RuntimeError):
    pass


def url_do_banco(url: str) -> str:
    for antigo in ("postgres://", "postgresql://"):
        if url.startswith(antigo):
            return "postgresql+psycopg://" + url[len(antigo) :]
    return url


@dataclass(frozen=True)
class Configuracao:
    database_url: str
    admin_token: str


def carregar() -> Configuracao:
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        raise ConfiguracaoAusente("DATABASE_URL não está definida: a API não tem de onde ler.")
    token = (os.environ.get("DADOS_API_ADMIN_TOKEN") or "").strip()
    if len(token) < TAMANHO_MINIMO_DO_TOKEN:
        raise ConfiguracaoAusente(
            f"DADOS_API_ADMIN_TOKEN precisa de {TAMANHO_MINIMO_DO_TOKEN} caracteres ou mais: "
            "sem ele, as rotas de administração ficariam abertas ou mortas."
        )
    return Configuracao(database_url=url_do_banco(url), admin_token=token)
