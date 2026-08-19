from pydantic import BaseModel, Field


class PassiveIncomeMonth(BaseModel):
    month: str = Field(..., description="Formato YYYY-MM")
    portfolio_value: float = Field(..., description="Valor total da carteira")
    passive_income_monthly: float = Field(..., description="Renda passiva mensal (R$)")
    passive_income_yearly: float = Field(..., description="Renda passiva anual (R$)")
    dividend_yield_avg: float = Field(..., description="Dividend yield médio (%)")


class PassiveIncomeProjectionRequest(BaseModel):
    monthly_contribution: float = Field(0.0, ge=0, description="Aporte mensal adicional (R$)")
    target_monthly_income: float | None = Field(
        None, ge=0, description="Meta de renda passiva mensal (R$)"
    )
    dividend_growth_rate: float = Field(
        0.05, ge=0, le=0.30, description="Taxa anual de crescimento dos dividendos"
    )
    portfolio_growth_rate: float = Field(
        0.10, ge=0, le=0.50, description="Taxa anual de valorização da carteira"
    )
    reinvest_dividends: bool = Field(True, description="Reinvestir dividendos automaticamente")
    months_ahead: int = Field(60, ge=1, le=240, description="Meses de projeção (padrão: 5 anos)")


class PassiveIncomeProjectionResponse(BaseModel):
    current_passive_income_monthly: float = Field(
        ..., description="Renda passiva mensal atual (R$)"
    )
    current_passive_income_yearly: float = Field(..., description="Renda passiva anual atual (R$)")
    current_portfolio_value: float = Field(..., description="Valor atual da carteira (R$)")
    current_dividend_yield_avg: float = Field(..., description="Dividend yield médio atual (%)")

    projections: list[PassiveIncomeMonth] = Field(..., description="Projeções mês a mês")

    target_monthly_income: float | None = Field(
        None, description="Meta de renda passiva mensal (R$)"
    )
    months_to_target: int | None = Field(None, description="Meses para atingir a meta")
    target_date: str | None = Field(None, description="Data estimada para atingir meta (YYYY-MM)")

    assumptions: dict = Field(default_factory=dict, description="Premissas utilizadas na projeção")
