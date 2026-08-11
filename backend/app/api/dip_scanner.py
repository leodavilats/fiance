import asyncio
import json

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.models import DipScannerResponse
from app.services import DipService

router = APIRouter()

dip_service = DipService()


@router.get("/dip-scanner", response_model=DipScannerResponse)
async def dip_scanner(
    universe: str | None = Query(
        None, description="Tickers separados por vírgula. Padrão: universo do sistema"
    ),
    min_score: float = Query(
        40.0, ge=0, le=100, description="Score mínimo para incluir no resultado"
    ),
    top: int = Query(12, ge=1, le=30, description="Máximo de itens retornados"),
    category: str | None = Query(
        None, description="Filtrar por categoria: acoes_br | acoes_int | fiis | cripto"
    ),
) -> DipScannerResponse:
    result = await dip_service.scan_dips(universe, min_score, top)

    if category:
        from app.analysis.classify import auto_category

        result.items = [
            item
            for item in result.items
            if auto_category(
                item.asset_type.value
                if hasattr(item.asset_type, "value")
                else str(item.asset_type),
                None,
            )
            == category
        ]

    return result


@router.get("/dip-scanner/stream")
async def dip_scanner_stream(
    universe: str | None = Query(None),
    min_score: float = Query(40.0, ge=0, le=100),
    top: int = Query(12, ge=1, le=30),
    category: str | None = Query(None),
) -> StreamingResponse:
    async def event_generator():
        found = 0
        scanned = 0
        async for event in dip_service.scan_dips_stream(universe, min_score, top, category):
            if event.get("type") == "item":
                found += 1
            if event.get("type") == "summary":
                scanned = event.get("scanned", 0)
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0)
        yield f"data: {json.dumps({'type': 'done', 'found': found, 'scanned': scanned})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
