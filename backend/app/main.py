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
        version="1.0.0",
        description="Análise fundamentalista e recomendação de carteira (B3).",
        lifespan=lifespan,
    )

    app.middleware("http")(observability_middleware)

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

    app.include_router(router, prefix="/api")

    return app


app = create_app()
