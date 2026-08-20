from pydantic import BaseModel, Field

from .opportunity import Opportunity
from .portfolio import PortfolioPosition, PortfolioSnapshot


class Alert(BaseModel):
    """Alerta do dashboard, agrupado e com um desfecho.

    Antes o dashboard emitia alertas sem limite nem deduplicação — um por
    posição SELL, um por setor acima de 30%, um por categoria fora da meta — e a
    única ação oferecida na tela era "ir para Mercado". Muita carga cognitiva,
    nenhum desfecho.
    """

    severity: str
    kind: str
    title: str
    detail: str
    ticker: str | None = None
    # Quantos itens o alerta representa (3 posições com sinal de venda vira uma
    # linha, não três).
    count: int = 1
    tickers: list[str] = Field(default_factory=list)
    # Ação sugerida: analyze | sell | rebalance | goals | market | fixed_income
    action: str | None = None
    action_label: str | None = None


class CategoryAllocation(BaseModel):
    category: str
    current_value: float
    current_pct: float
    target_pct: float | None = None
    delta_pct: float | None = None
    delta_value: float | None = None


class PortfolioHealth(BaseModel):
    score: float = Field(..., description="Score de saúde da carteira, 0-100")
    concentration_score: float
    sector_concentration_score: float
    diversification_score: float
    risk_score: float
    top_position_ticker: str | None = None
    top_position_pct: float | None = None
    top_sector: str | None = None
    top_sector_pct: float | None = None
    warnings: list[str] = Field(default_factory=list)


class DashboardSummary(BaseModel):
    total_invested: float
    total_current: float
    total_pnl: float
    total_pnl_pct: float

    monthly_dividends_estimate: float
    yearly_dividends_estimate: float = 0.0
    portfolio_yield: float | None = None
    passive_income_goal: float | None = None
    passive_income_progress: float | None = None

    positions_count: int


class DataFreshness(BaseModel):
    """Frescor e origem do dado que alimentou a tela.

    `get_rates()` já devolvia `source: bcb | estimativa` — o único indicador de
    proveniência do sistema — e nenhuma tela o mostrava. O usuário não
    distinguia cotação de agora de cotação de 2 h atrás.
    """

    rates_source: str = "estimativa"
    market_data_age_seconds: float | None = None
    market_data_stale: bool = False
    quotes_ttl_seconds: int = 0


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    positions: list[PortfolioPosition]
    top_buys: list[Opportunity]
    top_sells: list[PortfolioPosition]
    alerts: list[Alert]
    allocations: list[CategoryAllocation]
    snapshots: list[PortfolioSnapshot]
    health: PortfolioHealth | None = None
    freshness: DataFreshness | None = None
    last_updated: float | None = None
    disclaimer: str = "Conteúdo educativo. Não constitui recomendação formal de investimento."
