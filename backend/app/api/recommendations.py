"""Controller para recomendações de investimento."""

from fastapi import APIRouter, HTTPException

from app.models import RecommendRequest, RecommendResponse
from app.services import RecommendationService

router = APIRouter()

recommendation_service = RecommendationService()


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest) -> RecommendResponse:
    """Gera recomendação de portfolio."""
    try:
        return await recommendation_service.recommend(req)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, str(e))


@router.post("/analyze")
async def analyze(req: RecommendRequest) -> dict:
    """Analisa o universo e retorna ranking."""
    return await recommendation_service.analyze(req)
