from typing import List, Optional
from pydantic import BaseModel, Field

from .enums import AssetType
from .analysis import FairPriceBlock, TechnicalBlock


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
    name: Optional[str] = None
    sector: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    fair_price: FairPriceBlock
    technical: TechnicalBlock
    fundamentals: dict = Field(default_factory=dict)
    dip_score: float = Field(..., description="Score total 0-100")
    breakdown: DipScoreBreakdownSchema
    verdict: str = Field(..., description="OPORTUNIDADE | NEUTRO | ARMADILHA")
    verdict_label: str
    confidence: float
    reasons: List[str] = Field(default_factory=list)
    drop_from_52w_high_pct: Optional[float] = None
    drop_from_fair_price_pct: Optional[float] = None
    news: List[NewsItemSchema] = Field(default_factory=list)
    news_sentiment_summary: str = ""
    news_ai_summary: Optional[str] = Field(None, description="Resumo gerado por IA das notícias")
    news_ai_score: Optional[float] = Field(None, description="Score de sentimento por IA (0-10)")
    news_impact: Optional[str] = Field(None, description="Impacto estimado: high/medium/low")
    news_key_topics: List[str] = Field(default_factory=list, description="Tópicos principais identificados")
    disclaimer: str = (
        "Conteúdo educativo. Não constitui recomendação formal de investimento."
    )


class DipScanItem(BaseModel):
    symbol: str
    name: Optional[str] = None
    asset_type: AssetType
    sector: Optional[str] = None
    price: Optional[float] = None
    fair_price_consensus: Optional[float] = None
    margin_of_safety: Optional[float] = None
    dip_score: float
    breakdown: DipScoreBreakdownSchema
    verdict: str
    verdict_label: str
    confidence: float
    drop_from_52w_high_pct: Optional[float] = None
    drop_from_fair_price_pct: Optional[float] = None
    dividend_yield: Optional[float] = None
    rsi_14: Optional[float] = None
    top_reason: str = ""


class DipScannerResponse(BaseModel):
    items: List[DipScanItem]
    scanned: int
    universe_used: List[str]
    disclaimer: str = (
        "Conteúdo educativo. Não constitui recomendação formal de investimento."
    )
