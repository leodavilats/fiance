from typing import List, Optional
from pydantic import BaseModel, Field

from .enums import AssetType


class FairPriceBlock(BaseModel):
    bazin: Optional[float] = None
    graham: Optional[float] = None
    consensus: Optional[float] = None
    margin_of_safety: Optional[float] = None
    avg_dividend_5y: Optional[float] = None
    details: dict = Field(default_factory=dict)


class TechnicalBlock(BaseModel):
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    rsi_14: Optional[float] = None
    trend: str = "unknown"
    last_price: Optional[float] = None
    distance_from_52w_high_pct: Optional[float] = None
    distance_from_52w_low_pct: Optional[float] = None


class DecisionBlock(BaseModel):
    verdict: str
    label: str
    confidence: float
    reasons: List[str] = Field(default_factory=list)


class AssetAnalysis(BaseModel):
    symbol: str
    asset_type: AssetType
    name: Optional[str] = None
    sector: Optional[str] = None
    currency: Optional[str] = None
    price: Optional[float] = None
    fundamentals: dict = Field(default_factory=dict)
    fair_price: FairPriceBlock
    technical: TechnicalBlock
    decision: DecisionBlock
