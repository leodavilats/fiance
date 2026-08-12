from fastapi import APIRouter

from app.models import BenchmarkResponse
from app.services import BenchmarkService

router = APIRouter()


@router.get("/benchmark", response_model=BenchmarkResponse)
async def benchmark() -> BenchmarkResponse:
    svc = BenchmarkService()
    return await svc.get_benchmark()
