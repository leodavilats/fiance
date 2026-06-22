from pydantic import BaseModel, Field

from .enums import AssetType


class Opportunity(BaseModel):
    ticker: str
    name: str | None = None
    asset_type: AssetType
    sector: str | None = None
    price: float | None = None
    fair_price: float | None = None
    bazin: float | None = None
    graham: float | None = None
    margin_of_safety: float | None = None
    dividend_yield: float | None = None
    verdict: str
    label: str
    category_resolved: str = "acoes_br"
    score: float = 0.0
    in_portfolio: bool = False
    is_interesting: bool = False
    reasons: list[str] = Field(default_factory=list)
    suggested_quantity: int | None = None
    suggested_invest: float | None = None


class OpportunitiesResponse(BaseModel):
    items: list[Opportunity]
    cash_available: float
    total_items: int = 0
    total_pages: int = 0
    current_page: int = 1
    page_size: int = 50
