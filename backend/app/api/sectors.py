from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services import OpportunityService

router = APIRouter()

_service = OpportunityService()


class SectorAsset(BaseModel):
    ticker: str
    name: str | None = None
    score: float = 0.0
    price: float | None = None
    dividend_yield: float | None = None
    verdict: str = ""
    label: str = ""


class SectorSummary(BaseModel):
    sector: str
    count: int
    avg_score: float
    avg_dy: float
    top_assets: list[SectorAsset]


class SectorsSummaryResponse(BaseModel):
    sectors: list[SectorSummary]
    total_assets: int
    failed_count: int


@router.get("/sectors-summary", response_model=SectorsSummaryResponse)
async def sectors_summary(
    category: str = Query(
        "acoes_br",
        description="Filtrar por categoria: acoes_br | fiis | acoes_int | cripto",
    ),
) -> SectorsSummaryResponse:
    response = await _service.get_opportunities(
        page=1,
        page_size=1000,
        category=category,
        sort_by="score",
    )

    sectors_map: dict[str, dict] = {}

    for opp in response.items:
        sector = opp.sector or "Outros"
        if sector not in sectors_map:
            sectors_map[sector] = {"assets": [], "scores": [], "dys": []}
        sectors_map[sector]["assets"].append(opp)
        sectors_map[sector]["scores"].append(opp.score)
        if opp.dividend_yield is not None:
            sectors_map[sector]["dys"].append(opp.dividend_yield)

    result: list[SectorSummary] = []
    for sector, data in sorted(sectors_map.items(), key=lambda x: -len(x[1]["assets"])):
        assets = data["assets"]
        top = sorted(assets, key=lambda o: o.score or 0, reverse=True)[:5]
        scores = data["scores"]
        dys = data["dys"]
        result.append(
            SectorSummary(
                sector=sector,
                count=len(assets),
                avg_score=round(sum(scores) / len(scores), 1) if scores else 0.0,
                avg_dy=round(sum(dys) / len(dys), 2) if dys else 0.0,
                top_assets=[
                    SectorAsset(
                        ticker=o.ticker,
                        name=o.name,
                        score=o.score,
                        price=o.price,
                        dividend_yield=o.dividend_yield,
                        verdict=o.verdict,
                        label=o.label,
                    )
                    for o in top
                ],
            )
        )

    return SectorsSummaryResponse(
        sectors=result,
        total_assets=response.total_items,
        failed_count=response.failed_count,
    )
