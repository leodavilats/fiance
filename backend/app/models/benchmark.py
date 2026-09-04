from pydantic import BaseModel, Field


class BenchmarkPoint(BaseModel):
    date: str = Field(..., description="Formato YYYY-MM-DD")
    portfolio_pct: float = Field(
        ..., description="Retorno acumulado da carteira (%), ponderado no tempo"
    )
    cdi_pct: float = Field(..., description="Retorno acumulado do CDI no período (%)")
    ibov_pct: float | None = Field(None, description="Retorno acumulado do Ibovespa (%)")
    invested: float = Field(0.0, description="Total aportado até a data")
    patrimony: float = Field(0.0, description="Patrimônio na data")


class BenchmarkResponse(BaseModel):
    points: list[BenchmarkPoint]
    ibov_available: bool = Field(
        ..., description="Se o Ibovespa pôde ser buscado (fonte externa pode falhar)"
    )
    cdi_source: str = Field(
        "bcb",
        description=(
            "Origem da taxa que gerou a curva de CDI: bcb | bcb_cache_vencido | estimativa."
        ),
    )
    cdi_basis: str = Field(
        "taxa_atual_composta",
        description=(
            "Como a curva foi construída. `taxa_atual_composta` extrapola a taxa de hoje "
            "para trás: é referência, não o CDI acumulado histórico."
        ),
    )
    portfolio_return_pct: float = 0.0
    cdi_return_pct: float = 0.0
    ibov_return_pct: float | None = None
    net_contributions: float = Field(
        0.0, description="Aportes líquidos no período (não contam como rentabilidade)"
    )
    method: str = Field(
        "twr",
        description="Metodologia do retorno da carteira: twr = ponderado no tempo",
    )
