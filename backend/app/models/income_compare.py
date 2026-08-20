from pydantic import BaseModel, Field

"""Comparação de renda: renda fixa e ativos de bolsa na mesma tela.

O comparador de RF (`/renda-fixa/comparar`) e o de ativos (`/opportunities`)
eram universos separados. Com `taxa_liquida_aa` de um lado e DY + margem de
segurança do outro, dava para responder "com a Selic a 14,4%, vale mais o CDB ou
o FII?" — a pergunta que define a alocação de quase todo investidor brasileiro —
e o produto nunca colocava os dois lados na mesma conta.
"""


class IncomeOption(BaseModel):
    kind: str = Field(..., description="renda_fixa | acao | fii | bdr | etf")
    label: str
    ticker: str | None = None

    # Eixo 1: renda recorrente líquida esperada, em % a.a. É o único número
    # comparável diretamente entre renda fixa e ativos de bolsa.
    net_income_yield_pct: float
    income_basis: str = Field(
        ..., description="Como o rendimento foi apurado (taxa contratada, DY dos últimos 12m…)"
    )

    # Eixo 2: valorização potencial. Renda fixa não tem — deixar explícito
    # evita a comparação errada de somar as duas coisas.
    upside_pct: float | None = None
    has_upside: bool = False

    liquidity: str = Field(..., description="diaria | no_vencimento | bolsa")
    tax_note: str = ""
    risk_note: str = ""

    monthly_income_estimate: float = 0.0
    score: float | None = None
    data_completeness: float | None = None


class IncomeCompareResponse(BaseModel):
    amount: float
    horizon_months: int
    cdi_anual: float
    ipca_anual: float
    rates_source: str = "estimativa"

    fixed_income: list[IncomeOption] = Field(default_factory=list)
    assets: list[IncomeOption] = Field(default_factory=list)

    best_income_option: IncomeOption | None = None
    verdict: str = ""
    disclaimer: str = (
        "Comparação de renda recorrente. Renda fixa tem retorno contratado; ativos de "
        "bolsa oscilam e o dividend yield futuro não é garantido. Conteúdo educativo."
    )
