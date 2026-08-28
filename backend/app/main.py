from __future__ import annotations

import asyncio
import contextlib
import logging
import traceback
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.errors import DomainError
from app.core.jobs import start_background_jobs
from app.core.observability import observability_middleware

logger = logging.getLogger("fiance")

#: Versão do contrato da API. Muda quando uma resposta deixa de ser
#: retrocompatível — campo removido ou renomeado, semântica alterada. Campo
#: **adicionado** não muda a versão: cliente que não o conhece o ignora.
API_VERSION = "v1"


def _purge_legacy_fixed_income() -> None:
    from app.storage import portfolio_store

    try:
        removed = portfolio_store.purge_legacy_fixed_income_tickers()
        if removed:
            logger.info(
                "Renda fixa migrou para tabela própria: %d posição(ões) RF_* legadas removidas.",
                removed,
            )
    except Exception:
        logger.warning("Falha ao limpar posições RF_* legadas", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    _purge_legacy_fixed_income()

    tasks = start_background_jobs()
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        for task in tasks:
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task


def create_app() -> FastAPI:

    settings = get_settings()
    settings.validate_for_startup()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    app = FastAPI(
        title="fiance",
        version=f"1.{API_VERSION.lstrip('v')}.0",
        description="Análise fundamentalista e recomendação de carteira (B3).",
        lifespan=lifespan,
    )

    app.middleware("http")(observability_middleware)

    @app.middleware("http")
    async def stamp_api_version(request: Request, call_next):
        """Carimba a versão e diz se o cliente veio pelo caminho sem versão.

        `X-API-Deprecation` existe para ser medido, não para ser lido por
        humano: é o que permite saber quando o alias `/api` pode sair sem
        derrubar ninguém.
        """
        response = await call_next(request)
        response.headers["X-API-Version"] = API_VERSION
        path = request.url.path
        if path.startswith("/api/") and not path.startswith(f"/api/{API_VERSION}/"):
            # Sem acento de propósito: cabeçalho HTTP é latin-1, e um "á" aqui
            # derruba a resposta inteira com UnicodeDecodeError.
            response.headers["X-API-Deprecation"] = f"deprecated; use /api/{API_VERSION}{path[4:]}"
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept"],
    )

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        logger.warning("%s em %s: %s", type(exc).__name__, request.url.path, exc)
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        logger.warning("ValueError em %s: %s", request.url.path, exc)
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Erro inesperado em %s: %s\n%s",
            request.url.path,
            exc,
            traceback.format_exc(),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno do servidor. Tente novamente mais tarde."},
        )

    # Duas montagens do **mesmo** router, não duas cópias da API.
    #
    # `/api/v1` é o caminho canônico: sem versão no caminho, uma mudança de
    # contrato só tem dois destinos ruins — quebrar cliente publicado ou nunca
    # mudar. `/api` continua respondendo porque os apps instalados apontam para
    # lá, e derrubá-los num deploy seria trocar um problema por outro.
    #
    # O alias não é permanente: sai quando a telemetria mostrar que não há mais
    # cliente antigo chamando. Até lá, a resposta carrega `X-API-Version` para
    # que dê para medir isso.
    app.include_router(router, prefix=f"/api/{API_VERSION}")
    app.include_router(router, prefix="/api", include_in_schema=False)

    return app


app = create_app()
