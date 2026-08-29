from fastapi import APIRouter

from app.models.whats_new import WhatsNewResponse
from app.services.whats_new_service import WhatsNewService

router = APIRouter()


@router.get("/whats-new", response_model=WhatsNewResponse)
async def whats_new() -> WhatsNewResponse:
    return await WhatsNewService().build()
