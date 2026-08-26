from pydantic import BaseModel, Field

from .analysis import FairPriceBlock, TechnicalBlock
from .enums import AssetType


class NewsItemSchema(BaseModel):
    title: str
    source: str
    published: str
    url: str
    sentiment: str


class DipScoreBreakdownSchema(BaseModel):
    value_score: float = Field(..., description="Margem de segurança (0-30)")
    quality_score: float = Field(..., description="Fundamentos (0-25)")
    technical_score: float = Field(..., description="Técnico / RSI / 52w (0-25)")
    dividend_score: float = Field(..., description="Dividendos (0-10)")
    news_score: float = Field(..., description="Sentimento de notícias (0-10)")


class DipAnalysisResponse(BaseModel):
    symbol: str
    asset_type: AssetType
    name: str | None = None
    sector: str | None = None
    price: float | None = None
    currency: str | None = None
    fair_price: FairPriceBlock
    technical: TechnicalBlock
    fundamentals: dict = Field(default_factory=dict)
    dip_score: float = Field(..., description="Score total 0-100")
    breakdown: DipScoreBreakdownSchema
    verdict: str = Field(..., description="OPORTUNIDADE | NEUTRO | ARMADILHA")
    verdict_label: str
    confidence: float
    reasons: list[str] = Field(default_factory=list)
    reason_groups: dict[str, list[str]] = Field(
        default_factory=dict,
        description=(
            "Os mesmos motivos de `reasons`, agrupados pela dimensão que os gerou "
            "(value, quality, technical, dividend, news). Permite ao cliente separar "
            "queda aritmética de deterioração de fundamento."
        ),
    )
    drop_from_52w_high_pct: float | None = None
    drop_from_fair_price_pct: float | None = None
    news: list[NewsItemSchema] = Field(default_factory=list)
    news_sentiment_summary: str = ""
    news_ai_summary: str | None = Field(None, description="Resumo gerado por IA das notícias")
    news_ai_score: float | None = Field(None, description="Score de sentimento por IA (0-10)")
    news_impact: str | None = Field(None, description="Impacto estimado: high/medium/low")
    news_key_topics: list[str] = Field(
        default_factory=list, description="Tópicos principais identificados"
    )
    disclaimer: str = "Conteúdo educativo. Não constitui recomendação formal de investimento."


class DipScanItem(BaseModel):
    symbol: str
    name: str | None = None
    asset_type: AssetType
    sector: str | None = None
    price: float | None = None
    fair_price_consensus: float | None = None
    margin_of_safety: float | None = None
    dip_score: float
    breakdown: DipScoreBreakdownSchema
    verdict: str
    verdict_label: str
    confidence: float
    drop_from_52w_high_pct: float | None = None
    drop_from_fair_price_pct: float | None = None
    dividend_yield: float | None = None
    rsi_14: float | None = None
    top_reason: str = ""


class DipScannerResponse(BaseModel):
    items: list[DipScanItem]
    scanned: int
    universe_used: list[str]
    disclaimer: str = "Conteúdo educativo. Não constitui recomendação formal de investimento."
