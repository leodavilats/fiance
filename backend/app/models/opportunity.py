from typing import List, Optional
from pydantic import BaseModel, Field

from .enums import AssetType


class Opportunity(BaseModel):
    ticker: str
    name: Optional[str] = None
    asset_type: AssetType
    sector: Optional[str] = None
    price: Optional[float] = None
    fair_price: Optional[float] = None
    margin_of_safety: Optional[float] = None
    dividend_yield: Optional[float] = None
    verdict: str
    label: str
    category_resolved: str = "trade"
    score: float = 0.0
    in_watchlist: bool = False
    in_portfolio: bool = False
    is_interesting: bool = False
    reasons: List[str] = Field(default_factory=list)
    suggested_quantity: Optional[int] = None
    suggested_invest: Optional[float] = None


class OpportunitiesResponse(BaseModel):
    items: List[Opportunity]
    cash_available: float
    total_items: int = 0
    total_pages: int = 0
    current_page: int = 1
    page_size: int = 50
