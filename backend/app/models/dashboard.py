from typing import List, Optional
from pydantic import BaseModel, Field

from .portfolio import PortfolioPosition, PortfolioSnapshot
from .opportunity import Opportunity


class Alert(BaseModel):
    severity: str
    kind: str
    title: str
    detail: str
    ticker: Optional[str] = None


class CategoryAllocation(BaseModel):
    category: str
    current_value: float
    current_pct: float
    target_pct: Optional[float] = None
    delta_pct: Optional[float] = None
    delta_value: Optional[float] = None


class DashboardSummary(BaseModel):
    total_invested: float
    total_current: float
    total_pnl: float
    total_pnl_pct: float
    cash_available: float
    monthly_dividends_estimate: float
    portfolio_yield: Optional[float] = None
    positions_count: int


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    positions: List[PortfolioPosition]
    top_buys: List[Opportunity]
    top_sells: List[PortfolioPosition]
    alerts: List[Alert]
    allocations: List[CategoryAllocation]
    snapshots: List[PortfolioSnapshot]
    last_updated: Optional[float] = None
    disclaimer: str = (
        "Conteúdo educativo. Não constitui recomendação formal de investimento."
    )
