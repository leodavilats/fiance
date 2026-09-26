from __future__ import annotations

from pydantic import BaseModel, Field

from .portfolio import StoredPortfolioItem


class LedgerEntryOut(BaseModel):
    id: int | None = None
    kind: str
    symbol: str
    traded_on: str
    quantity: float = 0.0
    price: float = 0.0
    fees: float = 0.0
    ratio_from: float = 1.0
    ratio_to: float = 1.0
    amount: float = 0.0
    note: str | None = None


class TransactionsPage(BaseModel):
    items: list[LedgerEntryOut] = Field(default_factory=list)
    count: int
    next_cursor: str | None = None
    has_more: bool = False


class TransactionCreated(BaseModel):
    id: int


class TransactionsCreated(BaseModel):
    ids: list[int] = Field(default_factory=list)
    count: int


class PositionProjectionOut(BaseModel):
    symbol: str
    quantity: float
    avg_price: float
    total_cost: float
    realized_pnl: float
    total_fees: float
    first_traded_on: str | None = None
    last_traded_on: str | None = None
    entries_applied: int
    warnings: list[str] = Field(default_factory=list)


class DerivationStepOut(BaseModel):
    traded_on: str
    kind: str
    description: str
    quantity_after: float
    total_cost_after: float
    avg_price_after: float


class PositionDerivation(BaseModel):
    symbol: str
    position: PositionProjectionOut
    steps: list[DerivationStepOut] = Field(default_factory=list)


class ReconciliationDifference(BaseModel):
    ticker: str
    reason: str
    stored: StoredPortfolioItem | None = None
    projected: PositionProjectionOut | None = None


class Reconciliation(BaseModel):
    positions: int
    projected: int
    differences: list[ReconciliationDifference] = Field(default_factory=list)
    in_sync: bool


class BackfillResult(BaseModel):
    seeded: int


class RebuildResult(BaseModel):
    rebuilt: int
    reconciliation: Reconciliation


class ImportIssueOut(BaseModel):
    line: int
    message: str
    field: str | None = None
    raw: str = ""


class ImportRowOut(BaseModel):
    line: int
    kind: str
    symbol: str
    traded_on: str
    quantity: float
    price: float
    fees: float
    ratio_from: float
    ratio_to: float
    amount: float
    note: str | None = None
    duplicate_of: int | None = None


class ImportPreview(BaseModel):
    format: str
    rows: list[ImportRowOut] = Field(default_factory=list)
    issues: list[ImportIssueOut] = Field(default_factory=list)
    ok: bool
    duplicates: int


class ImportCommitted(BaseModel):
    imported: int
    skipped_duplicates: int
    ids: list[int] = Field(default_factory=list)
