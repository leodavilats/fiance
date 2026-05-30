from pydantic import BaseModel


class DividendRankingItem(BaseModel):
    ticker: str
    name: str | None
    sector: str | None
    price: float | None
    dividend_yield_12m: float | None
    total_dividends_12m: float | None
    fair_price_bazin: float | None = None
    verdict: str | None = None


class DividendRankingResponse(BaseModel):
    items: list[DividendRankingItem]
