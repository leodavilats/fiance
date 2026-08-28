from pydantic import BaseModel, Field

from .enums import AssetType

MAX_PORTFOLIO_ITEMS = 500

TICKER_PATTERN = r"^[A-Za-z][A-Za-z0-9]{3}\d{1,2}$"


class PortfolioItem(BaseModel):
    ticker: str = Field(
        ...,
        min_length=4,
        max_length=32,
        pattern=TICKER_PATTERN,
        description="Ex.: PETR4, HGLG11, AAPL34",
    )
    quantity: float = Field(..., gt=0)
    avg_price: float = Field(..., gt=0, description="Preço médio pago")
    category: str = Field(
        "auto",
        max_length=32,
        description="renda_fixa | acoes_br | bdrs | fiis | etfs | auto",
    )


class PortfolioEvaluationRequest(BaseModel):
    items: list[PortfolioItem] = Field(..., max_length=MAX_PORTFOLIO_ITEMS)


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
    confidence: float = 0.0
    data_years: int = 0
    consensus_methods: int = 0
    trend_basis: str = "none"
    as_of: float | None = None
    reasons: list[str] = Field(default_factory=list)
    category: str = "auto"
    category_resolved: str = "acoes_br"
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
    """Importação explícita: substitui a carteira inteira."""

    items: list[PortfolioItem] = Field(..., min_length=1, max_length=MAX_PORTFOLIO_ITEMS)


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


class SellRequest(BaseModel):
    ticker: str = Field(..., min_length=4, max_length=32, pattern=TICKER_PATTERN)
    quantity: float = Field(..., gt=0)
    sell_price: float = Field(..., gt=0)
    sold_at: float | None = Field(
        None, description="Timestamp da venda (passado, até 90 dias atrás); default = agora"
    )


class ClosedTrade(BaseModel):
    id: int
    ticker: str
    category: str
    quantity: float
    avg_price: float
    sell_price: float
    gross_profit: float
    ir_rate: float
    ir_amount: float
    net_profit: float
    loss_offset_used: float = 0.0
    taxable_profit: float = 0.0
    loss_compensable: bool = True
    sold_at: float


class TaxLossCategoryBalance(BaseModel):
    """Saldo de prejuízo realizado por categoria, disponível para compensar."""

    category: str
    realized_loss: float
    offset_used: float
    available: float


class ClosedTradesResponse(BaseModel):
    trades: list[ClosedTrade]

    #: Totais sobre a tabela inteira, **não** sobre a página. Um total que
    #: encolhe conforme o usuário rola é pior que uma lista longa.
    total_realized_pnl: float
    total_ir_paid: float
    tax_loss_balances: list[TaxLossCategoryBalance] = Field(default_factory=list)
    total_tax_loss_available: float = 0.0

    next_cursor: str | None = Field(
        default=None,
        description="Passe em `cursor` para a próxima página. `null` quando acabou.",
    )
    has_more: bool = False
    total_count: int = 0
