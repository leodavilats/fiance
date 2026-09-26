from typing import Any

from pydantic import BaseModel, Field


class DeletedById(BaseModel):
    deleted: int


class DeletedByTicker(BaseModel):
    deleted: str


class SessionRevoked(BaseModel):
    revoked: str


class ActivityItem(BaseModel):
    id: int
    action: str
    entity: str | None = None
    entity_id: str | None = None
    summary: str | None = None
    detail: dict[str, Any] = Field(default_factory=dict)
    occurred_at: float


class ActivityLog(BaseModel):
    items: list[ActivityItem] = Field(default_factory=list)


class AccountDeleted(BaseModel):
    deleted: bool
    removed: dict[str, int]
    sla_days: int


class DeletionPolicy(BaseModel):
    sla_days: int
    removes: list[str]
    note: str
    confirmation_phrase: str


class EventsAccepted(BaseModel):
    accepted: int


class EventSpecOut(BaseModel):
    name: str
    question: str
    description: str


class EventCatalog(BaseModel):
    questions: list[str]
    events: list[EventSpecOut]


class AhaCandidates(BaseModel):
    candidates: list[dict]


class CircuitStatus(BaseModel):
    provider: str
    state: str
    consecutive_failures: int
    rejected_while_open: int
    last_failure: str | None = None
    retry_in_seconds: float | None = None


class PlausibilityRange(BaseModel):
    field: str
    low: float
    high: float
    reason: str
    rejects_snapshot: bool


class SourceHealth(BaseModel):
    circuit: CircuitStatus
    plausibility_ranges: list[PlausibilityRange]


class PlanRule(BaseModel):
    feature: str
    min_plan: str
    free_limit: int | None = None
    premium_limit: int | None = None
    unit: str | None = None
    monthly: bool
    rationale: str


class PlanRules(BaseModel):
    rules: list[PlanRule]


class FeatureCheck(BaseModel):
    allowed: bool
    feature: str
    plan: str
    required_plan: str
    reason: str | None = None
    limit: int | None = None
    used: int | None = None
    limit_reached: bool


class UniverseList(BaseModel):
    tickers: list[str]


class UniverseMatch(BaseModel):
    ticker: str
    name: str | None = None


class UniverseSearch(BaseModel):
    items: list[UniverseMatch]


class CacheCleared(BaseModel):
    message: str
    deleted: int


class MetricsReset(BaseModel):
    reset: bool


class SubscriptionSummary(BaseModel):
    status: str
    plan_code: str
    interval: str | None = None
    price_cents: int
    locked: bool
    current_period_end: float | None = None


class EntitlementsState(BaseModel):
    plan: str
    unrestricted: bool
    in_trial: bool
    trial_ends_at: float | None = None
    trial_days_left: int | None = None
    credited_until: float | None = None
    price_cents: int
    locked_price: bool
    features: dict[str, bool] = Field(default_factory=dict)
    limits: dict[str, int | None] = Field(default_factory=dict)
    subscription: SubscriptionSummary
