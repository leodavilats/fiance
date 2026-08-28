from pydantic import BaseModel, Field


class PassiveIncomeMonth(BaseModel):
    """Um mês da projeção consolidada — sempre com a faixa junto.

    Os campos ``_low`` e ``_high`` são obrigatórios de propósito. Se tivessem
    default, existiria um caminho em que o número sai sozinho, e é exatamente
    esse caminho que empresta precisão de centavo a uma pilha de premissas.
    """

    month: str = Field(..., description="Formato YYYY-MM")

    portfolio_value: float = Field(..., description="Valor da carteira no cenário base (R$)")
    portfolio_value_low: float = Field(..., description="Piso entre os cenários (R$)")
    portfolio_value_high: float = Field(..., description="Teto entre os cenários (R$)")

    passive_income_monthly: float = Field(..., description="Renda mensal no cenário base (R$)")
    passive_income_monthly_low: float = Field(..., description="Piso entre os cenários (R$)")
    passive_income_monthly_high: float = Field(..., description="Teto entre os cenários (R$)")

    passive_income_yearly: float = Field(..., description="Renda anual no cenário base (R$)")
    dividend_yield_avg: float = Field(..., description="Dividend yield médio (%)")


class ScenarioMonth(BaseModel):
    """Um mês dentro de um cenário. Carrega o código do cenário para não haver
    número sem a premissa que o gerou."""

    scenario: str = Field(..., description="Código do cenário que produziu o número")
    month: str = Field(..., description="Formato YYYY-MM")
    portfolio_value: float = Field(..., description="Valor total da carteira (R$)")
    passive_income_monthly: float = Field(..., description="Renda passiva mensal (R$)")


class ScenarioSeries(BaseModel):
    code: str = Field(..., description="conservador | base | otimista")
    label: str = Field(..., description="Nome exibível")
    rationale: str = Field(..., description="A premissa, em uma frase — nunca ocultável")
    portfolio_growth_rate: float = Field(..., description="Valorização anual usada")
    dividend_growth_rate: float = Field(..., description="Crescimento anual de dividendos usado")
    months: list[ScenarioMonth] = Field(..., description="Série mês a mês")
    final_passive_income_monthly: float = Field(..., description="Renda mensal no último mês (R$)")
    final_portfolio_value: float = Field(..., description="Carteira no último mês (R$)")
    months_to_target: int | None = Field(None, description="Meses até a meta neste cenário")
    target_date: str | None = Field(None, description="Data estimada (YYYY-MM) neste cenário")


class TargetEstimate(BaseModel):
    """A data da meta como faixa.

    ``latest_months`` nulo significa "não chega dentro do horizonte projetado" —
    e essa é uma resposta útil, não uma falha. Omitir o cenário que não chega
    faria a meta parecer garantida.
    """

    monthly_income: float = Field(..., description="Meta de renda passiva mensal (R$)")
    earliest_months: int | None = Field(None, description="No cenário mais favorável")
    expected_months: int | None = Field(None, description="No cenário base")
    latest_months: int | None = Field(None, description="No cenário conservador; nulo = não chega")
    earliest_date: str | None = Field(None, description="YYYY-MM")
    expected_date: str | None = Field(None, description="YYYY-MM")
    latest_date: str | None = Field(None, description="YYYY-MM")
    reached_in_all_scenarios: bool = Field(
        ..., description="Falso quando algum cenário não alcança a meta no horizonte"
    )


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

    projections: list[PassiveIncomeMonth] = Field(
        ..., description="Cenário base mês a mês, cada ponto com piso e teto"
    )
    scenarios: list[ScenarioSeries] = Field(..., description="As três contas, declaradas")

    target: TargetEstimate | None = Field(None, description="A meta como faixa de datas")
    target_monthly_income: float | None = Field(
        None, description="Meta de renda passiva mensal (R$)"
    )

    disclaimer: str = Field(..., description="Por que isto é uma faixa e não uma previsão")
    assumptions: dict = Field(default_factory=dict, description="Premissas utilizadas na projeção")
