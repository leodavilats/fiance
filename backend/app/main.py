from __future__ import annotations

import asyncio
import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import router
from app.core.config import get_settings
from app.core.database import init_db


def create_app() -> FastAPI:

    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    app = FastAPI(
        title="fiance",
        version="1.0.0",
        description="Análise fundamentalista e recomendação de carteira (B3).",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept"],
    )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        logging.getLogger("fiance").warning("ValueError em %s: %s", request.url.path, exc)
        msg = str(exc).lower()
        status = 404 if ("não encontrado" in msg or "not found" in msg or "nenhum" in msg) else 400
        return JSONResponse(status_code=status, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logging.getLogger("fiance").error(
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

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

        async def _warm_up_opportunities() -> None:
            from app.services import OpportunityService

            try:
                await OpportunityService()._scan_universe({})
                logging.getLogger("fiance").info("Cache de oportunidades aquecido no startup.")
            except Exception:
                logging.getLogger("fiance").warning(
                    "Falha ao aquecer cache de oportunidades no startup", exc_info=True
                )

        asyncio.create_task(_warm_up_opportunities())

        async def _notification_loop() -> None:
            from app.services.notification_job import run_notification_cycle

            # Espera o warm-up preencher o cache pra não pagar o scan completo 2x.
            await asyncio.sleep(60)
            while True:
                try:
                    await run_notification_cycle()
                except Exception:
                    logging.getLogger("fiance").warning(
                        "Falha no ciclo de notificações", exc_info=True
                    )
                await asyncio.sleep(15 * 60)

        asyncio.create_task(_notification_loop())

    return app


app = create_app()
