from __future__ import annotations

from pydantic import BaseModel, Field

from app.cashflow import (
    CATEGORIAS_DE_DESPESA,
    CATEGORIAS_DE_ENTRADA,
    TIPOS_DE_DIVIDA,
)

_DATA = r"^\d{4}-\d{2}-\d{2}$"
_MES = r"^\d{4}-\d{2}$"


class CashEntryRequest(BaseModel):
    kind: str = Field(..., pattern="^(income|expense)$")
    category: str
    description: str = Field(..., min_length=1, max_length=120)
    amount: float = Field(..., gt=0, description="Sempre positivo: o sinal vem de `kind`.")
    due_on: str = Field(..., pattern=_DATA)
    paid_on: str | None = Field(None, pattern=_DATA)


class CashEntryResponse(BaseModel):
    id: int
    kind: str
    category: str
    description: str
    amount: float
    due_on: str
    paid_on: str | None
    derived: bool


class CashEntryBatchRequest(BaseModel):
    entries: list[CashEntryRequest] = Field(..., min_length=1, max_length=200)


class TemplateCandidateResponse(BaseModel):
    kind: str
    category: str
    description: str
    amount: float
    due_on: str = Field(
        ..., description="Já no mês de destino, preso ao último dia quando preciso."
    )
    repeats: bool = Field(
        ...,
        description=(
            "Se a categoria volta todo mês por natureza. Gasto variável não volta: ele é fato do "
            "mês que passou, e copiá-lo inventaria despesa."
        ),
    )
    already_there: bool


class MonthTemplateResponse(BaseModel):
    source: str
    target: str
    candidates: list[TemplateCandidateResponse]


class MarkPaidRequest(BaseModel):
    paid_on: str | None = Field(None, pattern=_DATA)


class EstimateResponse(BaseModel):
    base_months: list[str]
    expected_low: float
    expected_high: float
    spent_so_far: float
    remaining_low: float
    remaining_high: float


class DueEntryResponse(BaseModel):
    id: int | None
    category: str
    description: str
    amount: float
    due_on: str


class MonthResponse(BaseModel):
    month: str
    received: float
    paid: float
    committed: float

    free_now: float = Field(
        ...,
        description=(
            "Fato: entrou, menos saiu, menos o comprometido e datado. Não tem faixa porque não "
            "é projeção."
        ),
    )

    surplus_low: float = Field(
        ..., description="Projeção: o piso da sobra, que é o número sobre o qual a ordem decide."
    )
    surplus_high: float
    has_range: bool = Field(
        ...,
        description=(
            "Falso quando não há mês fechado para estimar. Ausência de estimativa não vira "
            "zero: a sobra passa a ser o próprio `free_now`."
        ),
    )

    income_baseline: float = Field(
        ..., description="A renda recorrente: exclui provento e reembolso."
    )
    estimate: EstimateResponse
    due: list[DueEntryResponse]


class DebtRequest(BaseModel):
    kind: str
    description: str = Field(..., min_length=1, max_length=120)
    balance: float = Field(..., gt=0)
    monthly_rate: float | None = Field(
        None,
        ge=0,
        description=(
            "Percentual ao mês. Nulo quer dizer **não informada** — o produto não estima taxa "
            "de rotativo, e sem ela a régua não aparece."
        ),
    )


class DebtResponse(BaseModel):
    id: int | None
    kind: str
    description: str
    balance: float
    monthly_rate: float | None

    debt_class: str = Field(
        ...,
        alias="class",
        description="expensive | manageable | no_rate — derivado da taxa, nunca do tipo.",
    )
    reference_monthly: float | None
    reference_source: str
    flip_rate: float | None = Field(
        ..., description="A taxa em que o veredito muda. Sai por álgebra, não por opinião."
    )

    model_config = {"populate_by_name": True}


class StepResponse(BaseModel):
    order: int
    type: str = Field(..., description="debt | reserve | contribution")
    amount: float
    reason: str
    falsifier: str | None
    reference: str | None


class CascadeResponse(BaseModel):
    surplus_low: float
    steps: list[StepResponse] = Field(
        ...,
        description=(
            "Pode vir **sem** passo de aporte, e isso é resposta: com dívida cara consumindo a "
            "sobra inteira, a ordem certa é não aportar."
        ),
    )
    available_to_invest: float


class SurplusResponse(BaseModel):
    month: MonthResponse
    cascade: CascadeResponse
    has_cash: bool = Field(
        ...,
        description=(
            "Falso quando não há lançamento próprio. A tela então pede o valor **e diz por que "
            "está pedindo**."
        ),
    )


class CashVocabularyResponse(BaseModel):
    expense_categories: list[str] = list(CATEGORIAS_DE_DESPESA)
    income_categories: list[str] = list(CATEGORIAS_DE_ENTRADA)
    debt_kinds: list[str] = list(TIPOS_DE_DIVIDA)
