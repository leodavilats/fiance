from datetime import date

from pydantic import BaseModel, Field

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
    ticker: str = Field(..., min_length=4, max_length=32, pattern=TICKER_PATTERN)
    source: str = Field("opportunities", max_length=32)
    action: str = Field("comprar", max_length=32, description="comprar | vender | realocar")
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0, description="Preço executado")
    followed_on: date | None = Field(None, description="Default: hoje")
    score_at_suggestion: float | None = Field(None, ge=0, le=100)
    verdict_at_suggestion: str | None = Field(None, max_length=32)
    note: str | None = Field(None, max_length=200)


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
