from fastapi import APIRouter

from app.models.followed import (
    FollowedSuggestion,
    FollowedSuggestionCreate,
    FollowedSuggestionsResponse,
)
from app.services.followed_service import FollowedService

router = APIRouter()

service = FollowedService()


@router.get("/suggestions/followed", response_model=FollowedSuggestionsResponse)
async def followed_outcomes() -> FollowedSuggestionsResponse:
    """Resultado das sugestões que o usuário seguiu, contra o Ibovespa.

    Fecha o ciclo decisão -> execução -> resultado: o produto passa a ser
    auditável pelo próprio usuário.
    """
    return await service.outcomes()


@router.post("/suggestions/followed", response_model=FollowedSuggestion, status_code=201)
async def register_followed(req: FollowedSuggestionCreate) -> FollowedSuggestion:
    return service.register(req)


@router.delete("/suggestions/followed/{suggestion_id}")
async def delete_followed(suggestion_id: int) -> dict:
    return service.delete(suggestion_id)
