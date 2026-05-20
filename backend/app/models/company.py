from typing import Optional
from pydantic import BaseModel, Field


class CompanyFundamentals(BaseModel):
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    price: Optional[float] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = None
    dividend_yield: Optional[float] = None
    debt_to_equity: Optional[float] = None
    profit_margin: Optional[float] = None
    revenue_growth: Optional[float] = None


class ScoredCompany(BaseModel):
    fundamentals: CompanyFundamentals
    score: float = Field(..., description="Score composto 0-100")
    breakdown: dict = Field(default_factory=dict)
    rationale: str = ""
