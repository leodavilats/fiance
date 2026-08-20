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

logger = logging.getLogger("fiance")


async def _warm_up_opportunities() -> None:
    from app.services import OpportunityService

    try:
        # Aquece só o dado de mercado (independe de preferência) — a
        # personalização é calculada por request.
        await OpportunityService()._scan_market()
        logger.info("Cache de oportunidades aquecido no startup.")
    except Exception:
        logger.warning("Falha ao aquecer cache de oportunidades no startup", exc_info=True)


async def _notification_loop() -> None:
    from app.services.notification_job import run_notification_cycle

    # Espera o warm-up preencher o cache pra não pagar o scan completo 2x.
    await asyncio.sleep(60)
    while True:
        try:
            await run_notification_cycle()
        except Exception:
            logger.warning("Falha no ciclo de notificações", exc_info=True)
        await asyncio.sleep(15 * 60)


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

    tasks = [
        asyncio.create_task(_warm_up_opportunities(), name="warm-up-opportunities"),
        asyncio.create_task(_notification_loop(), name="notification-loop"),
    ]
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
        # Só o path e o traceback — o corpo da request pode carregar dado
        # financeiro do usuário e não deve entrar no log.
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
