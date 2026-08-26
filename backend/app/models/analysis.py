from pydantic import BaseModel, Field

from .enums import AssetType


class FairPriceBlock(BaseModel):
    bazin: float | None = None
    graham: float | None = None
    dcf: float | None = None
    consensus: float | None = None
    margin_of_safety: float | None = None
    avg_dividend_5y: float | None = None
    dy_12m: float | None = None
    dy_5y: float | None = None
    data_years: int = 0
    desired_yield_used: float = 0.06
    pvp: float | None = None
    consensus_methods: int = 0
    details: dict = Field(default_factory=dict)


class TechnicalBlock(BaseModel):
    sma_50: float | None = None
    sma_200: float | None = None
    rsi_14: float | None = None
    trend: str = "unknown"
    trend_basis: str = "none"
    last_price: float | None = None
    distance_from_52w_high_pct: float | None = None
    distance_from_52w_low_pct: float | None = None


class DecisionBlock(BaseModel):
    verdict: str
    label: str
    confidence: float
    reasons: list[str] = Field(default_factory=list)


class PricePoint(BaseModel):
    """Um fechamento diário. `date` em ISO (AAAA-MM-DD)."""

    date: str
    close: float


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
    price_history: list[PricePoint] = Field(
        default_factory=list,
        description=(
            "Fechamentos diários usados no bloco técnico. Já eram buscados para calcular "
            "médias móveis e descartados em seguida — sem eles o cliente não tem como "
            "desenhar preço contra preço justo. Vem preenchido só no endpoint de um ativo; "
            "em /compare fica vazio, porque N séries completas não cabem numa comparação."
        ),
    )


class CompareResponse(BaseModel):
    items: list[AssetAnalysis] = Field(default_factory=list)
    errors: list[str] = Field(
        default_factory=list, description="Tickers que falharam ao buscar/analisar"
    )
