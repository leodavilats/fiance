from __future__ import annotations

import logging
import re

from app.core.observability import _SIGILO_NA_URL

logger = logging.getLogger("fiance.telemetry")

CAMPOS_DE_REQUEST_PERMITIDOS = frozenset({"method", "url"})

CABECALHOS_PERMITIDOS = frozenset({"x-request-id", "user-agent", "content-type"})

_SEGMENTO_IDENTIFICADOR = re.compile(
    r"^(?:[A-Z][A-Z0-9]{3}\d{1,2}|\d+|[0-9a-fA-F-]{16,})$",
)

_DINHEIRO = re.compile(r"R\$\s?-?[\d.,]+")

_NUMERO_ENTRE_PARENTESES = re.compile(r"\((-?\d[\d.,]*)\)")


def limpar_caminho(url: str) -> str:
    if "://" in url:
        esquema, resto = url.split("://", 1)
        if "/" not in resto:
            return url
        host, caminho = resto.split("/", 1)
        prefixo = f"{esquema}://{host}/"
    else:
        prefixo, caminho = ("/", url.lstrip("/")) if url.startswith("/") else ("", url)

    caminho = caminho.split("?", 1)[0]
    partes = [
        "{id}" if _SEGMENTO_IDENTIFICADOR.match(parte) else parte for parte in caminho.split("/")
    ]
    return prefixo + "/".join(partes)


def limpar_texto(texto: str) -> str:
    limpo = _SIGILO_NA_URL.sub(r"\1=[redigido]", texto)
    limpo = _DINHEIRO.sub("R$ [redigido]", limpo)
    return _NUMERO_ENTRE_PARENTESES.sub("([redigido])", limpo)


def limpar_evento(evento: dict, _hint: dict | None = None) -> dict:
    request = evento.get("request")
    if isinstance(request, dict):
        limpo = {
            chave: valor
            for chave, valor in request.items()
            if chave in CAMPOS_DE_REQUEST_PERMITIDOS
        }
        if isinstance(limpo.get("url"), str):
            limpo["url"] = limpar_caminho(limpo["url"])

        cabecalhos = request.get("headers")
        if isinstance(cabecalhos, dict):
            limpo["headers"] = {
                nome: valor
                for nome, valor in cabecalhos.items()
                if nome.lower() in CABECALHOS_PERMITIDOS
            }
        evento["request"] = limpo

    usuario = evento.get("user")
    if isinstance(usuario, dict):
        evento["user"] = {"id": usuario["id"]} if usuario.get("id") else {}

    for trilha in evento.get("breadcrumbs", {}).get("values", []) or []:
        if not isinstance(trilha, dict):
            continue
        trilha.pop("data", None)
        if isinstance(trilha.get("message"), str):
            trilha["message"] = limpar_texto(trilha["message"])

    if isinstance(evento.get("message"), str):
        evento["message"] = limpar_texto(evento["message"])

    for excecao in evento.get("exception", {}).get("values", []) or []:
        if isinstance(excecao, dict) and isinstance(excecao.get("value"), str):
            excecao["value"] = limpar_texto(excecao["value"])

    evento.pop("extra", None)
    for excecao in evento.get("exception", {}).get("values", []) or []:
        for frame in (excecao.get("stacktrace") or {}).get("frames", []) or []:
            if isinstance(frame, dict):
                frame.pop("vars", None)

    return evento


class SentryNaoInstalado(RuntimeError):
    pass


def configurar_sentry() -> bool:
    from app.core.config import get_settings

    settings = get_settings()
    dsn = (settings.sentry_dsn or "").strip()
    if not dsn:
        logger.info("SENTRY_DSN vazio — telemetria de erro desligada.")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
    except ImportError as exc:
        raise SentryNaoInstalado(
            "SENTRY_DSN configurado, mas o pacote `sentry-sdk` não está instalado. "
            "Instale-o (está no requirements.txt) ou apague a variável — subir achando que "
            "está observado e não estar é pior que subir cego assumidamente."
        ) from exc

    sentry_sdk.init(
        dsn=dsn,
        environment=settings.app_env,
        release=settings.release or None,
        send_default_pii=False,
        max_request_body_size="never",
        traces_sample_rate=settings.sentry_traces_sample_rate,
        before_send=limpar_evento,
        before_send_transaction=limpar_evento,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
    )
    logger.info("Sentry ligado em %s.", settings.app_env)
    return True
