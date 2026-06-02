from pydantic import BaseModel, Field


class QuickInvestRequest(BaseModel):
    cash_available: float = Field(..., gt=0, description="Caixa disponível para investir (R$)")
    use_current_goals: bool = Field(True, description="Usar metas de alocação salvas")
    prioritize_rebalance: bool = Field(True, description="Priorizar rebalanceamento da carteira")
    min_order_value: float = Field(100.0, ge=0, description="Valor mínimo por ordem (R$)")


class QuickInvestAllocation(BaseModel):
    ticker: str
    name: str | None
    category: str
    sector: str | None
    current_price: float
    suggested_quantity: int
    suggested_investment: float
    rationale: str = Field(..., description="Por que investir neste ativo")
    score: float | None = None
    dividend_yield: float | None = None


class QuickInvestResponse(BaseModel):
    total_cash: float = Field(..., description="Caixa total disponível (R$)")
    allocated_cash: float = Field(..., description="Caixa alocado nas sugestões (R$)")
    remaining_cash: float = Field(..., description="Caixa restante (R$)")

    allocations: list[QuickInvestAllocation] = Field(..., description="Sugestões de compra")

    portfolio_balance: dict = Field(
        default_factory=dict, description="Balanço da carteira após investimento"
    )

    summary: str = Field(..., description="Resumo executivo da estratégia")
