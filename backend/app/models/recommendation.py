from typing import List, Optional
from pydantic import BaseModel, Field

from .enums import RiskProfile, OptimizationStrategy


class RecommendRequest(BaseModel):
    cash: float = Field(..., gt=0, description="Caixa disponível em BRL")
    profile: RiskProfile = RiskProfile.moderate
    max_positions: int = Field(8, ge=1, le=30)
    universe: Optional[List[str]] = Field(
        None, description="Tickers B3 (sem .SA). Usa padrão se omitido."
    )
    exclude_sectors: List[str] = Field(default_factory=list)
    strategy: OptimizationStrategy = OptimizationStrategy.score_weighted
    explain: bool = Field(False, description="Pedir racional textual via LLM (requer OPENAI_API_KEY).")


class Allocation(BaseModel):
    ticker: str
    name: Optional[str]
    sector: Optional[str]
    price: float
    quantity: int
    invested: float
    weight: float
    score: float
    rationale: str


class RecommendResponse(BaseModel):
    profile: RiskProfile
    strategy: OptimizationStrategy
    cash_input: float
    cash_invested: float
    cash_remaining: float
    allocations: List[Allocation]
    metrics: dict = Field(default_factory=dict)
    explanation: str = ""
    disclaimer: str = (
        "Este conteúdo é apenas informativo e não constitui recomendação "
        "formal de investimento. Consulte um profissional habilitado."
    )
