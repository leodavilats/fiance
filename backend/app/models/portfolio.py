from typing import List, Optional
from pydantic import BaseModel, Field

from .enums import AssetType


class PortfolioItem(BaseModel):
    ticker: str = Field(..., description="Ex.: PETR4, AAPL, BTC, HGLG11")
    quantity: float = Field(..., gt=0)
    avg_price: float = Field(..., gt=0, description="Preço médio pago")
    category: str = Field("auto", description="'renda', 'trade' ou 'auto'")


class PortfolioEvaluationRequest(BaseModel):
    items: List[PortfolioItem]
    desired_yield: float = Field(0.06, gt=0, le=0.30)


class PortfolioPosition(BaseModel):
    ticker: str
    name: Optional[str]
    asset_type: AssetType
    quantity: float
    avg_price: float
    current_price: Optional[float]
    invested: float
    current_value: Optional[float]
    pnl: Optional[float]
    pnl_pct: Optional[float]
    fair_price: Optional[float]
    margin_of_safety: Optional[float]
    verdict: str
    label: str
    reasons: List[str] = Field(default_factory=list)
    category: str = "auto"
    category_resolved: str = "trade"
    dividend_yield: Optional[float] = None
    sector: Optional[str] = None


class PortfolioEvaluationResponse(BaseModel):
    positions: List[PortfolioPosition]
    total_invested: float
    total_current: float
    total_pnl: float
    total_pnl_pct: float
    disclaimer: str = (
        "Conteúdo educativo. Não constitui recomendação formal de investimento."
    )


class StoredPortfolioItem(BaseModel):
    ticker: str
    quantity: float
    avg_price: float
    category: str = "auto"
    updated_at: Optional[float] = None


class SavePortfolioRequest(BaseModel):
    items: List[PortfolioItem]


class PortfolioSnapshot(BaseModel):
    captured_at: float
    total_invested: float
    total_current: float
    total_pnl: float
    total_pnl_pct: float


class PortfolioStateResponse(BaseModel):
    items: List[StoredPortfolioItem]
    last_updated: Optional[float] = None
    snapshots: List[PortfolioSnapshot] = Field(default_factory=list)
