from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/universe")
async def universe() -> dict:
    return {"tickers": get_settings().universe}
