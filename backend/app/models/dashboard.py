from pydantic import BaseModel

from .opportunity import Opportunity
from .portfolio import PortfolioPosition, PortfolioSnapshot


class Alert(BaseModel):
    severity: str
    kind: str
    title: str
    detail: str
    ticker: str | None = None


class CategoryAllocation(BaseModel):
    category: str
    current_value: float
    current_pct: float
    target_pct: float | None = None
    delta_pct: float | None = None
    delta_value: float | None = None


class DashboardSummary(BaseModel):
    total_invested: float
    total_current: float
    total_pnl: float
    total_pnl_pct: float
    cash_available: float

    # Métricas de Renda Passiva
    monthly_dividends_estimate: float
    yearly_dividends_estimate: float = 0.0
    portfolio_yield: float | None = None
    passive_income_goal: float | None = None
    passive_income_progress: float | None = None  # % da meta

    positions_count: int


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    positions: list[PortfolioPosition]
    top_buys: list[Opportunity]
    top_sells: list[PortfolioPosition]
    alerts: list[Alert]
    allocations: list[CategoryAllocation]
    snapshots: list[PortfolioSnapshot]
    last_updated: float | None = None
    disclaimer: str = "Conteúdo educativo. Não constitui recomendação formal de investimento."
