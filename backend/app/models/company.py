from pydantic import BaseModel, Field


class CompanyFundamentals(BaseModel):
    ticker: str
    name: str | None = None
    sector: str | None = None
    price: float | None = None
    market_cap: float | None = None
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    roe: float | None = None
    dividend_yield: float | None = None
    debt_to_equity: float | None = None
    profit_margin: float | None = None
    revenue_growth: float | None = None


class ScoredCompany(BaseModel):
    fundamentals: CompanyFundamentals
    score: float = Field(..., description="Score composto 0-100")
    breakdown: dict = Field(default_factory=dict)
    rationale: str = ""
