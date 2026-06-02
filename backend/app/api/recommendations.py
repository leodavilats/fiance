from fastapi import APIRouter, HTTPException

from app.models import RecommendRequest, RecommendResponse
from app.services import RecommendationService

router = APIRouter()

recommendation_service = RecommendationService()


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest) -> RecommendResponse:
    try:
        return await recommendation_service.recommend(req)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(502, str(e)) from e


@router.post("/analyze")
async def analyze(req: RecommendRequest) -> dict:
    return await recommendation_service.analyze(req)
