from pydantic import BaseModel, Field

from .enums import AssetType


class PortfolioItem(BaseModel):
    ticker: str = Field(..., description="Ex.: PETR4, AAPL, BTC, HGLG11")
    quantity: float = Field(..., gt=0)
    avg_price: float = Field(..., gt=0, description="Preço médio pago")
    category: str = Field("auto", description="'renda', 'trade' ou 'auto'")


class PortfolioEvaluationRequest(BaseModel):
    items: list[PortfolioItem]
    desired_yield: float = Field(0.06, gt=0, le=0.30)


class PortfolioPosition(BaseModel):
    ticker: str
    name: str | None
    asset_type: AssetType
    quantity: float
    avg_price: float
    current_price: float | None
    invested: float
    current_value: float | None
    pnl: float | None
    pnl_pct: float | None
    fair_price: float | None
    margin_of_safety: float | None
    verdict: str
    label: str
    reasons: list[str] = Field(default_factory=list)
    category: str = "auto"
    category_resolved: str = "trade"
    dividend_yield: float | None = None
    sector: str | None = None


class PortfolioEvaluationResponse(BaseModel):
    positions: list[PortfolioPosition]
    total_invested: float
    total_current: float
    total_pnl: float
    total_pnl_pct: float
    disclaimer: str = "Conteúdo educativo. Não constitui recomendação formal de investimento."


class StoredPortfolioItem(BaseModel):
    ticker: str
    quantity: float
    avg_price: float
    category: str = "auto"
    updated_at: float | None = None


class SavePortfolioRequest(BaseModel):
    items: list[PortfolioItem]


class PortfolioSnapshot(BaseModel):
    captured_at: float
    total_invested: float
    total_current: float
    total_pnl: float
    total_pnl_pct: float


class PortfolioStateResponse(BaseModel):
    items: list[StoredPortfolioItem]
    last_updated: float | None = None
    snapshots: list[PortfolioSnapshot] = Field(default_factory=list)
