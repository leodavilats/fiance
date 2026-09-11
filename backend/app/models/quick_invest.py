from pydantic import BaseModel, Field


class QuickInvestRequest(BaseModel):
    cash_available: float | None = Field(
        None,
        gt=0,
        description=(
            "Quanto aportar (R$). Nulo resolve da cascata do caixa: o que sobra depois da "
            "dívida caseira e da reserva."
        ),
    )
    min_order_value: float = Field(100.0, ge=0, description="Valor mínimo por ordem (R$)")


class QuickInvestAllocation(BaseModel):
    ticker: str
    name: str | None
    category: str
    sector: str | None
    current_price: float
    suggested_quantity: int
    suggested_investment: float
    rationale: str = Field(..., description="Por que este ativo, e não outro")
    score: float | None = None
    dividend_yield: float | None = None


class FixedIncomeSlice(BaseModel):
    amount: float
    reference_monthly_pct: float | None = Field(
        None, description="O que a referência rende ao mês, quando conhecida"
    )
    reference_source: str = Field(..., description="bcb, bcb_cache_vencido ou estimativa")
    rationale: str


class Unallocated(BaseModel):
    value: float
    reason: str


class QuickInvestResponse(BaseModel):
    total_cash: float = Field(..., description="Quanto entrou na conta (R$)")

    cash_source: str = Field(
        ...,
        description=(
            "'cascade' quando veio da sobra do mês; 'informed' quando a pessoa digitou o valor"
        ),
    )

    basis: str = Field(
        ...,
        description=(
            "'goals' quando a distribuição sai da alocação-alvo declarada; 'score' quando não há "
            "meta e a ordem é só por score"
        ),
    )

    allocated_cash: float
    remaining_cash: float

    allocations: list[QuickInvestAllocation] = Field(default_factory=list)

    fixed_income: FixedIncomeSlice | None = Field(
        None, description="A fatia de renda fixa, quando a alocação-alvo pede uma"
    )

    unallocated: list[Unallocated] = Field(
        default_factory=list, description="O que ficou sem destino, e por quê"
    )

    portfolio_balance: dict = Field(default_factory=dict)

    summary: str
