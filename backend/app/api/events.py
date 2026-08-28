from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core import events as event_catalog
from app.core.auth import get_current_user
from app.core.errors import DomainError
from app.services.analytics_service import aha_correlation, build_funnel
from app.storage import event_store

router = APIRouter()

admin_router = APIRouter()

# Um lote grande demais é sinal de cliente com fila represada, não de uso.
MAX_BATCH = 40


class EventIn(BaseModel):
    name: str
    props: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    platform: str = "web"
    occurred_at: float | None = None


class EventBatch(BaseModel):
    events: list[EventIn] = Field(default_factory=list)


class InvalidEventPayload(DomainError):
    status_code = 422


@router.post("/events")
async def ingest_events(body: EventBatch, user_id: str = Depends(get_current_user)) -> dict:
    """Recebe eventos de produto do cliente.

    Nome fora do dicionário e propriedade proibida devolvem 422 — falhar alto é
    de propósito: um evento aceito e descartado em silêncio vira uma métrica que
    ninguém sabe que está errada.
    """
    if len(body.events) > MAX_BATCH:
        raise InvalidEventPayload(f"No máximo {MAX_BATCH} eventos por lote.")

    now = time.time()
    accepted = 0
    for item in body.events:
        try:
            name, props = event_catalog.validate(item.name, item.props, item.platform)
        except event_catalog.InvalidEventError as exc:
            raise InvalidEventPayload(str(exc)) from exc

        # Relógio do cliente não define o passado: aceita-se até 24h de atraso
        # (fila offline do app) e nada no futuro.
        occurred_at = item.occurred_at or now
        occurred_at = min(max(occurred_at, now - 86400), now)

        event_store.record(user_id, name, props, item.platform, occurred_at=occurred_at)
        accepted += 1

    return {"accepted": accepted}


@router.get("/events/catalog")
async def read_catalog() -> dict:
    """O dicionário publicado — o cliente não inventa nome de evento."""
    return {"questions": list(event_catalog.QUESTIONS), "events": event_catalog.catalog_as_dicts()}


@admin_router.get("/analytics/funnel")
async def read_funnel(days: int = 90) -> dict:
    days = max(7, min(days, 400))
    return build_funnel(days=days)


@admin_router.get("/analytics/aha")
async def read_aha() -> dict:
    """Qual evento de aha prevê retenção — a pergunta que decide o paywall."""
    return {"candidates": aha_correlation()}
