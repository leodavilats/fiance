from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.collectors import circuit, plausibility
from app.services import OpportunityService

router = APIRouter()

_service = OpportunityService()

"""Instrumentação de qualidade do dado."""

_FIELD_IMPACT = {
    "price": "sem preço não há análise nenhuma",
    "dividend_yield": "sem DY o score de dividendos fica indefinido",
    "avg_dividend": "sem média de proventos não há Bazin (único método de ETF)",
    "eps": "sem LPA não há Graham nem DCF",
    "book_value": "sem VPA não há Graham nem P/VP",
    "roe": "sem ROE o score de qualidade perde metade da base",
    "profit_margin": "sem margem o score de qualidade perde metade da base",
    "debt_to_equity": "sem D/E o score de endividamento fica indefinido",
    "revenue_growth": "sem crescimento o DCF cai no default de 8%",
    "sector": "sem setor não há alerta de concentração setorial",
    "market_cap": "sem valor de mercado o score de liquidez fica indefinido",
    "technical_trend": "sem série longa a tendência é de curto prazo ou inexistente",
    "fair_price": "sem consenso não há margem de segurança, veredito nem alerta",
}


class FieldCoverage(BaseModel):
    field: str
    present: int
    total: int
    coverage_pct: float
    impact: str


class AssetTypeCoverage(BaseModel):
    asset_type: str
    count: int
    with_fair_price: int
    fair_price_coverage_pct: float


class DataQualityResponse(BaseModel):
    universe_size: int
    scanned: int
    failed: int
    fields: list[FieldCoverage] = Field(default_factory=list)
    by_asset_type: list[AssetTypeCoverage] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    source: dict = Field(
        default_factory=dict,
        description="Estado do disjuntor da fonte de cotação.",
    )
    plausibility: list[dict] = Field(
        default_factory=list,
        description="Faixa aceita por campo — o que está sendo barrado, e por quê.",
    )


@router.get("/data-quality/source")
async def source_health() -> dict:
    return {
        "circuit": circuit.status("brapi"),
        "plausibility_ranges": plausibility.describe_ranges(),
    }


@router.get("/data-quality", response_model=DataQualityResponse)
async def data_quality() -> DataQualityResponse:
    records, universe_size = await _service._scan_market()
    disjuntor = circuit.status("brapi")

    if not records:
        nota = (
            "Nenhum ativo coletado — o disjuntor da fonte está aberto, "
            "então as chamadas nem estão sendo tentadas."
            if disjuntor["state"] != "fechado"
            else "Nenhum ativo coletado — verifique o token da BRAPI e a conectividade."
        )
        return DataQualityResponse(
            universe_size=universe_size,
            scanned=0,
            failed=universe_size,
            notes=[nota],
            source=disjuntor,
            plausibility=plausibility.describe_ranges(),
        )

    total = len(records)
    present: dict[str, int] = dict.fromkeys(_FIELD_IMPACT, 0)

    by_type: dict[str, dict[str, int]] = {}

    for record in records:
        inputs = record.fair_inputs

        checks = {
            "price": record.price,
            "dividend_yield": record.dividend_yield,
            "avg_dividend": inputs.avg_dividend,
            "eps": inputs.eps,
            "book_value": inputs.book_value,
            "roe": record.roe,
            "profit_margin": record.profit_margin,
            "debt_to_equity": record.debt_to_equity,
            "revenue_growth": record.revenue_growth,
            "sector": record.sector,
            "market_cap": record.market_cap,
            "technical_trend": record.technical.trend_basis
            if record.technical.trend_basis != "none"
            else None,
            "fair_price": True
            if (inputs.avg_dividend or inputs.graham or inputs.dcf or inputs.pvp_fair)
            else None,
        }

        for field, value in checks.items():
            if value is not None:
                present[field] += 1

        bucket = by_type.setdefault(record.asset_type, {"count": 0, "with_fair_price": 0})
        bucket["count"] += 1
        if checks["fair_price"]:
            bucket["with_fair_price"] += 1

    fields = [
        FieldCoverage(
            field=field,
            present=count,
            total=total,
            coverage_pct=round(count / total * 100, 1),
            impact=_FIELD_IMPACT[field],
        )
        for field, count in sorted(present.items(), key=lambda kv: kv[1])
    ]

    by_asset_type = [
        AssetTypeCoverage(
            asset_type=asset_type,
            count=values["count"],
            with_fair_price=values["with_fair_price"],
            fair_price_coverage_pct=round(values["with_fair_price"] / values["count"] * 100, 1),
        )
        for asset_type, values in sorted(by_type.items())
    ]

    notes: list[str] = []
    etf = next((t for t in by_asset_type if t.asset_type == "etf"), None)
    if etf and etf.fair_price_coverage_pct < 50:
        notes.append(
            f"Só {etf.fair_price_coverage_pct:.0f}% dos ETFs têm preço justo: para ETF o "
            "Bazin é o único método, então a ausência de dividendsData na BRAPI apaga a "
            "análise inteira da classe."
        )

    dividends = next((f for f in fields if f.field == "avg_dividend"), None)
    if dividends and dividends.coverage_pct < 50:
        notes.append(
            f"Histórico de proventos presente em {dividends.coverage_pct:.0f}% do universo — "
            "confirme se `dividends` está liberado no plano da BRAPI em uso."
        )

    trend = next((f for f in fields if f.field == "technical_trend"), None)
    if trend and trend.coverage_pct < 100:
        notes.append(
            "Tendência indisponível em parte do universo: aumente BRAPI_HISTORY_RANGE "
            "(precisa de plano pago) para habilitar a SMA200."
        )

    if disjuntor["state"] != "fechado":
        notes.insert(
            0,
            f"Disjuntor da fonte em {disjuntor['state']}: as cotações vêm do cache, "
            "podem estar desatualizadas.",
        )

    return DataQualityResponse(
        universe_size=universe_size,
        scanned=total,
        failed=max(universe_size - total, 0),
        fields=fields,
        by_asset_type=by_asset_type,
        notes=notes,
        source=disjuntor,
        plausibility=plausibility.describe_ranges(),
    )
