from pydantic import BaseModel


class DeletedById(BaseModel):
    deleted: int


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
