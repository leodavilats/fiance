from __future__ import annotations

import logging

from fastapi import APIRouter, Query

from app.core.pagination import MAX_PAGE_SIZE
from app.models.inbox import InboxPage, InboxReadRequest, InboxUnread
from app.services import inbox_service
from app.storage import inbox_store

logger = logging.getLogger("fiance.inbox")

router = APIRouter()


@router.get("/inbox", response_model=InboxPage)
async def list_inbox(
    limit: int | None = Query(None, ge=1, le=MAX_PAGE_SIZE),
    cursor: str | None = Query(None, description="Cursor devolvido em `next_cursor`."),
    kind: list[str] | None = Query(None, description="Tipos a incluir. Repetir soma tipos."),
) -> dict:
    if cursor is None:
        try:
            await inbox_service.sync()
        except Exception:
            logger.warning("Não foi possível atualizar a caixa de avisos", exc_info=True)
    return inbox_service.page(limit, cursor, kind)


@router.get("/inbox/unread", response_model=InboxUnread)
async def unread_inbox() -> dict:
    return {"unread": inbox_store.unread_count()}


@router.post("/inbox/read", response_model=InboxUnread)
async def read_inbox(body: InboxReadRequest) -> dict:
    inbox_store.mark_read(body.ids)
    return {"unread": inbox_store.unread_count()}
