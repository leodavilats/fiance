from pydantic import BaseModel, Field

from .enums import AssetType


class FairPriceBlock(BaseModel):
    bazin: float | None = None
    graham: float | None = None
    consensus: float | None = None
    margin_of_safety: float | None = None
    avg_dividend_5y: float | None = None
    dy_12m: float | None = None
    dy_5y: float | None = None
    data_years: int = 0
    desired_yield_used: float = 0.06
    details: dict = Field(default_factory=dict)


class TechnicalBlock(BaseModel):
    sma_50: float | None = None
    sma_200: float | None = None
    rsi_14: float | None = None
    trend: str = "unknown"
    last_price: float | None = None
    distance_from_52w_high_pct: float | None = None
    distance_from_52w_low_pct: float | None = None


class DecisionBlock(BaseModel):
    verdict: str
    label: str
    confidence: float
    reasons: list[str] = Field(default_factory=list)


class AssetAnalysis(BaseModel):
    symbol: str
    asset_type: AssetType
    name: str | None = None
    sector: str | None = None
    currency: str | None = None
    price: float | None = None
    fundamentals: dict = Field(default_factory=dict)
    fair_price: FairPriceBlock
    technical: TechnicalBlock
    decision: DecisionBlock
