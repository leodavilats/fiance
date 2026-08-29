from fastapi import APIRouter, Query

from app.core.pagination import MAX_PAGE_SIZE
from app.models.followed import (
    FollowedSuggestion,
    FollowedSuggestionCreate,
    FollowedSuggestionsResponse,
)
from app.services.followed_service import FollowedService

router = APIRouter()

service = FollowedService()


@router.get("/suggestions/followed", response_model=FollowedSuggestionsResponse)
async def followed_outcomes(
    limit: int | None = Query(None, ge=1, le=MAX_PAGE_SIZE),
    cursor: str | None = Query(None, description="Cursor devolvido em `next_cursor`."),
) -> FollowedSuggestionsResponse:
    return await service.outcomes(limit=limit, cursor=cursor)


@router.post("/suggestions/followed", response_model=FollowedSuggestion, status_code=201)
async def register_followed(req: FollowedSuggestionCreate) -> FollowedSuggestion:
    return service.register(req)


@router.delete("/suggestions/followed/{suggestion_id}")
async def delete_followed(suggestion_id: int) -> dict:
    return service.delete(suggestion_id)
