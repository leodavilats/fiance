from __future__ import annotations

import logging

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from app.api import router

from app.core.config import get_settings

def create_app() -> FastAPI:

    settings = get_settings()

    logging.basicConfig(level=settings.log_level)

    app = FastAPI(

        title="fianceAI",

        version="0.1.0",

        description="Análise fundamentalista e recomendação de carteira (B3).",

    )

    app.add_middleware(

        CORSMiddleware,

        allow_origins=["*"],

        allow_methods=["*"],

        allow_headers=["*"],

    )

    app.include_router(router, prefix="/api")

    return app

app = create_app()

