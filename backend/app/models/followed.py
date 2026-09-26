from datetime import date
from typing import Self

from pydantic import BaseModel, Field, model_validator

from .portfolio import TICKER_PATTERN

SUGGESTION_SOURCES = (
    "opportunities",
    "rebalance",
    "quick_invest",
    "strategy",
    "dip_scanner",
    "whats_new",
)


class FollowedSuggestionCreate(BaseModel):
    ticker: str | None = Field(None, min_length=4, max_length=32, pattern=TICKER_PATTERN)
    entry_id: int | None = Field(
        None,
        description=(
            "Lançamento de compra ou venda do razão. Com ele, ativo, quantidade, preço e data "
            "saem do lançamento, e não são pedidos de novo."
        ),
    )
    source: str = Field("opportunities", max_length=32)
    action: str = Field("comprar", max_length=32, description="comprar | vender | realocar")
    quantity: float | None = Field(None, gt=0)
    price: float | None = Field(None, gt=0, description="Preço executado")
    followed_on: date | None = Field(None, description="Default: hoje")
    score_at_suggestion: float | None = Field(None, ge=0, le=100)
    verdict_at_suggestion: str | None = Field(None, max_length=32)
    note: str | None = Field(None, max_length=200)

    @model_validator(mode="after")
    def _do_razao_ou_digitada(self) -> Self:
        if self.entry_id is None and (
            self.ticker is None or self.quantity is None or self.price is None
        ):
            raise ValueError("Informe o lançamento do razão, ou ativo, quantidade e preço.")
        return self


class FollowedSuggestion(BaseModel):
    id: int
    ticker: str
    source: str
    action: str
    quantity: float
    price: float
    followed_on: date
    score_at_suggestion: float | None = None
    verdict_at_suggestion: str | None = None
    note: str | None = None
    entry_id: int | None = None

    invested: float = 0.0
    current_value: float | None = None
    pnl: float | None = None
    pnl_pct: float | None = None
    days_held: int = 0
    ibov_pct_since: float | None = None
    beat_ibov: bool | None = None


class SuggestionOutcomeGroup(BaseModel):
    source: str
    count: int
    invested: float
    current_value: float
    pnl: float
    pnl_pct: float
    ibov_pct: float | None = None


class FollowedSuggestionsResponse(BaseModel):
    items: list[FollowedSuggestion] = Field(default_factory=list)

    total_invested: float = 0.0
    total_current_value: float = 0.0
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0

    ibov_pct_same_period: float | None = None
    beat_ibov: bool | None = None

    by_source: list[SuggestionOutcomeGroup] = Field(default_factory=list)
    summary: str = ""

    next_cursor: str | None = None
    has_more: bool = False
    total_count: int = 0
