from typing import List, Optional
from pydantic import BaseModel


class DividendRankingItem(BaseModel):
    ticker: str
    name: Optional[str]
    sector: Optional[str]
    price: Optional[float]
    dividend_yield_12m: Optional[float]
    total_dividends_12m: Optional[float]
    fair_price_bazin: Optional[float] = None
    verdict: Optional[str] = None


class DividendRankingResponse(BaseModel):
    items: List[DividendRankingItem]
