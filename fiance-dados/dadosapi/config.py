from __future__ import annotations

import os
from dataclasses import dataclass

TAMANHO_MINIMO_DO_TOKEN = 32
ASAAS_PRODUCAO = "https://api.asaas.com/v3"


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
    cobranca_ativa: bool = False
    asaas_url: str = ASAAS_PRODUCAO
    asaas_chave: str = ""
    asaas_token_webhook: str = ""
    contato: str = ""
    proxies_confiaveis: int = 1


def _texto(nome: str) -> str:
    return (os.environ.get(nome) or "").strip()


def carregar() -> Configuracao:
    url = _texto("DATABASE_URL")
    if not url:
        raise ConfiguracaoAusente("DATABASE_URL não está definida: a API não tem de onde ler.")
    token = _texto("DADOS_API_ADMIN_TOKEN")
    if len(token) < TAMANHO_MINIMO_DO_TOKEN:
        raise ConfiguracaoAusente(
            f"DADOS_API_ADMIN_TOKEN precisa de {TAMANHO_MINIMO_DO_TOKEN} caracteres ou mais: "
            "sem ele, as rotas de administração ficariam abertas ou mortas."
        )
    ativa = _texto("COBRANCA_ATIVA").lower() == "true"
    chave, token_webhook = _texto("ASAAS_API_KEY"), _texto("ASAAS_WEBHOOK_TOKEN")
    if ativa and (not chave or len(token_webhook) < TAMANHO_MINIMO_DO_TOKEN):
        raise ConfiguracaoAusente(
            "COBRANCA_ATIVA=true exige ASAAS_API_KEY e ASAAS_WEBHOOK_TOKEN com 32 caracteres ou mais."
        )
    proxies = _texto("PROXIES_CONFIAVEIS") or "1"
    if not proxies.isdigit():
        raise ConfiguracaoAusente(
            "PROXIES_CONFIAVEIS precisa ser um inteiro: 0 usa o IP da conexão."
        )
    return Configuracao(
        database_url=url_do_banco(url),
        admin_token=token,
        cobranca_ativa=ativa,
        asaas_url=_texto("ASAAS_URL") or ASAAS_PRODUCAO,
        asaas_chave=chave,
        asaas_token_webhook=token_webhook,
        contato=_texto("CONTATO_EMAIL"),
        proxies_confiaveis=int(proxies),
    )
