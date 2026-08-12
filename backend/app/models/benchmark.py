from pydantic import BaseModel, Field


class BenchmarkPoint(BaseModel):
    date: str = Field(..., description="Formato YYYY-MM-DD")
    portfolio_pct: float = Field(..., description="Retorno acumulado da carteira (%)")
    cdi_pct: float = Field(..., description="Retorno acumulado do CDI no período (%)")
    ibov_pct: float | None = Field(None, description="Retorno acumulado do Ibovespa (%)")


class BenchmarkResponse(BaseModel):
    points: list[BenchmarkPoint]
    ibov_available: bool = Field(
        ..., description="Se o Ibovespa pôde ser buscado (fonte externa pode falhar)"
    )
    portfolio_return_pct: float = 0.0
    cdi_return_pct: float = 0.0
    ibov_return_pct: float | None = None
