from __future__ import annotations

from pydantic import BaseModel, Field

from .affirmation import AffirmationMode
from .enums import AssetType


class InvestorProfile(BaseModel):
    type: str
    description: str
    goals: dict[str, float] = Field(default_factory=dict)
    income_pct: float
    growth_pct: float
    risk_tolerance: str


class CategoryAllocationNow(BaseModel):
    category: str
    current_value: float
    current_pct: float
    assets_count: int


class AllocationGap(BaseModel):
    category: str
    target_pct: float
    current_pct: float
    gap_pct: float
    target_value: float
    current_value: float
    gap_value: float
    action: str | None = None


class StrategySuggestion(BaseModel):
    ticker: str
    name: str | None = None
    asset_type: AssetType
    category: str
    objective: str
    price: float | None = None
    quantity: int | None = None
    invest_amount: float | None = None
    score: float
    dividend_yield: float | None = None
    margin_of_safety: float | None = None
    verdict: str
    already_held: bool
    reasons: list[str] = Field(default_factory=list)
    rationale: str | None = None


class ReduceSuggestion(BaseModel):
    ticker: str
    name: str | None = None
    category: str
    verdict: str
    label: str | None = None
    quantity: float | None = None
    current_value: float | None = None
    pnl_pct: float | None = None
    overweight_category: bool
    reasons: list[str] = Field(default_factory=list)


class ProjectedAllocation(BaseModel):
    category: str
    projected_value: float | None = None
    projected_pct: float | None = None
    assets_count: int


class InvestmentStrategy(BaseModel):
    profile: InvestorProfile
    total_capital: float
    cash_available: float
    total_invested: float
    current_allocation: list[CategoryAllocationNow] = Field(default_factory=list)
    allocation_gaps: list[AllocationGap] = Field(default_factory=list)
    suggestions: list[StrategySuggestion] = Field(default_factory=list)
    reduce_suggestions: list[ReduceSuggestion] = Field(default_factory=list)
    projected_allocation: list[ProjectedAllocation] = Field(default_factory=list)
    summary: str
    affirmation: AffirmationMode


class RebalanceTarget(BaseModel):
    ticker: str
    name: str | None = None
    category: str
    score: float
    verdict: str


class RebalanceItem(BaseModel):
    ticker: str
    name: str | None = None
    category: str
    verdict: str
    action: str | None = None
    current_value: float | None = None
    quantity: float | None = None
    pnl_pct: float | None = None
    reasons: list[str] = Field(default_factory=list)
    realocar_para: RebalanceTarget | None = None
    requires_tax_review: bool


class RebalanceSuggestions(BaseModel):
    allocation_gaps: list[AllocationGap] = Field(default_factory=list)
    items: list[RebalanceItem] = Field(default_factory=list)
    tax_disclaimer: str | None = None
    affirmation: AffirmationMode
