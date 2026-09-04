from datetime import date

from pydantic import BaseModel, Field

from .portfolio import TICKER_PATTERN


class DividendReceivedBase(BaseModel):
    ticker: str = Field(..., min_length=4, max_length=32, pattern=TICKER_PATTERN)
    paid_at: date = Field(..., description="Data do crédito na conta")
    amount: float = Field(..., gt=0, le=1e9, description="Valor líquido recebido (R$)")
    kind: str = Field(
        "dividendo",
        max_length=32,
        description="dividendo | jcp | rendimento | amortizacao | outro",
    )
    note: str | None = Field(None, max_length=200)


class DividendReceivedCreate(DividendReceivedBase):
    pass


class DividendReceivedUpdate(BaseModel):
    ticker: str | None = Field(None, min_length=4, max_length=32, pattern=TICKER_PATTERN)
    paid_at: date | None = None
    amount: float | None = Field(None, gt=0, le=1e9)
    kind: str | None = Field(None, max_length=32)
    note: str | None = Field(None, max_length=200)


class DividendReceived(DividendReceivedBase):
    id: int


class DividendMonth(BaseModel):
    month: str = Field(..., description="YYYY-MM, no fuso brasileiro")
    total: float
    count: int


class DividendTickerTotal(BaseModel):
    ticker: str
    total: float
    count: int


class DividendsReceivedResponse(BaseModel):
    items: list[DividendReceived] = Field(default_factory=list)

    total_received: float = 0.0
    received_this_month: float = 0.0
    received_last_12m: float = 0.0
    monthly_average_12m: float = 0.0

    by_month: list[DividendMonth] = Field(default_factory=list)
    by_ticker: list[DividendTickerTotal] = Field(default_factory=list)

    estimated_monthly: float | None = None
    estimate_accuracy_pct: float | None = None

    next_cursor: str | None = None
    has_more: bool = False
    total_count: int = 0
