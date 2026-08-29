from __future__ import annotations

import time

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String, default="")
    picture: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[float] = mapped_column(Float, default=time.time)
    onboarded_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    deleted_at: Mapped[float | None] = mapped_column(Float, nullable=True)


class PortfolioPosition(Base):
    __tablename__ = "portfolio"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    ticker: Mapped[str] = mapped_column(String, primary_key=True)
    quantity: Mapped[float] = mapped_column(Float)
    avg_price: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String, default="auto")
    created_at: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[float] = mapped_column(Float)


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshot"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    captured_at: Mapped[float] = mapped_column(Float, primary_key=True)
    total_invested: Mapped[float] = mapped_column(Float)
    total_current: Mapped[float] = mapped_column(Float)
    total_pnl: Mapped[float] = mapped_column(Float)
    total_pnl_pct: Mapped[float] = mapped_column(Float)


class WatchlistItemDb(Base):
    __tablename__ = "watchlist"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    ticker: Mapped[str] = mapped_column(String, primary_key=True)
    note: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[float] = mapped_column(Float)


class GoalDb(Base):
    __tablename__ = "goals"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    category: Mapped[str] = mapped_column(String, primary_key=True)
    target_pct: Mapped[float] = mapped_column(Float)
    target_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    deadline: Mapped[str | None] = mapped_column(String, nullable=True)


class SectorGoalDb(Base):
    __tablename__ = "sector_goals"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    sector: Mapped[str] = mapped_column(String, primary_key=True)
    target_pct: Mapped[float] = mapped_column(Float)


class PreferencesDb(Base):
    __tablename__ = "preferences"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    cash_available: Mapped[float] = mapped_column(Float, default=0)
    passive_income_goal: Mapped[float | None] = mapped_column(Float, nullable=True)
    desired_yield_stock: Mapped[float] = mapped_column(Float, default=0.06)
    desired_yield_fii: Mapped[float] = mapped_column(Float, default=0.10)
    desired_yield_bdr: Mapped[float] = mapped_column(Float, default=0.04)
    desired_yield_etf: Mapped[float] = mapped_column(Float, default=0.04)
    notify_price_alerts: Mapped[bool] = mapped_column(default=True)
    opportunities_frequency: Mapped[str] = mapped_column(String, default="weekly")
    risk_profile: Mapped[str] = mapped_column(String, default="moderate")
    density: Mapped[str] = mapped_column(String, default="comfortable")
    preferred_categories: Mapped[str] = mapped_column(String, default="")
    preferred_sectors: Mapped[str] = mapped_column(String, default="")
    excluded_tickers: Mapped[str] = mapped_column(String, default="")
    last_digest_sent_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[float] = mapped_column(Float, default=time.time)


class ClosedTradeDb(Base):
    __tablename__ = "closed_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    ticker: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    quantity: Mapped[float] = mapped_column(Float)
    avg_price: Mapped[float] = mapped_column(Float)
    sell_price: Mapped[float] = mapped_column(Float)
    gross_profit: Mapped[float] = mapped_column(Float)
    ir_rate: Mapped[float] = mapped_column(Float)
    ir_amount: Mapped[float] = mapped_column(Float)
    net_profit: Mapped[float] = mapped_column(Float)
    loss_offset_used: Mapped[float] = mapped_column(Float, default=0.0)
    taxable_profit: Mapped[float] = mapped_column(Float, default=0.0)
    loss_compensable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sold_at: Mapped[float] = mapped_column(Float)
    created_at: Mapped[float] = mapped_column(Float)


class NotifiedOpportunityDb(Base):
    __tablename__ = "notified_opportunities"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    ticker: Mapped[str] = mapped_column(String, primary_key=True)
    notified_at: Mapped[float] = mapped_column(Float)


class DeviceTokenDb(Base):
    __tablename__ = "device_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    platform: Mapped[str] = mapped_column(String, default="android")
    created_at: Mapped[float] = mapped_column(Float)


class PriceAlertDb(Base):
    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    ticker: Mapped[str] = mapped_column(String)
    condition: Mapped[str] = mapped_column(String)
    target_price: Mapped[float] = mapped_column(Float)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[float] = mapped_column(Float)
    triggered_at: Mapped[float | None] = mapped_column(Float, nullable=True)


class FixedIncomePositionDb(Base):
    __tablename__ = "fixed_income_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    nome: Mapped[str] = mapped_column(String)
    tipo: Mapped[str] = mapped_column(String)
    valor_investido: Mapped[float] = mapped_column(Float)
    taxa: Mapped[float] = mapped_column(Float)
    tipo_taxa: Mapped[str] = mapped_column(String, default="pre_fixado")
    percentual_cdi: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_aplicacao: Mapped[str] = mapped_column(String)
    vencimento: Mapped[str | None] = mapped_column(String, nullable=True)
    liquidez: Mapped[str] = mapped_column(String, default="no_vencimento")
    isento_ir: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    oculto: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[float] = mapped_column(Float)


class JobLockDb(Base):
    __tablename__ = "job_locks"

    name: Mapped[str] = mapped_column(String, primary_key=True)
    holder: Mapped[str] = mapped_column(String)
    acquired_at: Mapped[float] = mapped_column(Float)
    expires_at: Mapped[float] = mapped_column(Float)


class DividendReceivedDb(Base):
    __tablename__ = "dividends_received"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    ticker: Mapped[str] = mapped_column(String, index=True)
    paid_at: Mapped[str] = mapped_column(String, index=True)
    amount: Mapped[float] = mapped_column(Float)
    kind: Mapped[str] = mapped_column(String, default="dividendo")
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[float] = mapped_column(Float)


class FollowedSuggestionDb(Base):
    __tablename__ = "followed_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    ticker: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[str] = mapped_column(String, default="opportunities")
    action: Mapped[str] = mapped_column(String, default="comprar")
    quantity: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    followed_on: Mapped[str] = mapped_column(String, index=True)
    score_at_suggestion: Mapped[float | None] = mapped_column(Float, nullable=True)
    verdict_at_suggestion: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[float] = mapped_column(Float)


class RevokedTokenDb(Base):
    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    revoked_at: Mapped[float] = mapped_column(Float)
    expires_at: Mapped[float] = mapped_column(Float, index=True)


class SessionCutDb(Base):
    __tablename__ = "session_cuts"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    cut_at: Mapped[float] = mapped_column(Float, nullable=False)


class UsageCounterDb(Base):
    __tablename__ = "usage_counters"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    resource: Mapped[str] = mapped_column(String, primary_key=True)
    window_key: Mapped[str] = mapped_column(String, primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expires_at: Mapped[float] = mapped_column(Float, index=True)
    updated_at: Mapped[float] = mapped_column(Float)


class ProductEventDb(Base):
    __tablename__ = "product_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    occurred_at: Mapped[float] = mapped_column(Float, index=True)
    day: Mapped[str] = mapped_column(String, index=True)
    platform: Mapped[str] = mapped_column(String, default="web")
    props: Mapped[str] = mapped_column(String, default="{}")


Index("ix_product_events_user_name", ProductEventDb.user_id, ProductEventDb.name)


class InstrumentDb(Base):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String, index=True)
    asset_type: Mapped[str] = mapped_column(String, default="br_stock")
    name: Mapped[str] = mapped_column(String, default="")
    isin: Mapped[str | None] = mapped_column(String, nullable=True)
    valid_from: Mapped[str] = mapped_column(String, default="1900-01-01")
    valid_to: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[float] = mapped_column(Float, default=time.time)


class TransactionDb(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    instrument_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    symbol: Mapped[str] = mapped_column(String, index=True)
    kind: Mapped[str] = mapped_column(String, index=True)
    quantity: Mapped[float] = mapped_column(Float, default=0.0)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    fees: Mapped[float] = mapped_column(Float, default=0.0)
    ratio_from: Mapped[float] = mapped_column(Float, default=1.0)
    ratio_to: Mapped[float] = mapped_column(Float, default=1.0)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    traded_on: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[str] = mapped_column(String, default="manual")
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[float] = mapped_column(Float)


Index("ix_transactions_user_symbol", TransactionDb.user_id, TransactionDb.symbol)
Index("ix_transactions_user_traded_on", TransactionDb.user_id, TransactionDb.traded_on)


class AuditLogDb(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    action: Mapped[str] = mapped_column(String, index=True)
    entity: Mapped[str] = mapped_column(String, default="")
    entity_id: Mapped[str | None] = mapped_column(String, nullable=True)
    summary: Mapped[str] = mapped_column(String, default="")
    detail: Mapped[str] = mapped_column(String, default="{}")
    occurred_at: Mapped[float] = mapped_column(Float, index=True)


class SubscriptionDb(Base):
    __tablename__ = "subscriptions"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)

    plan_code: Mapped[str] = mapped_column(String, default="free")
    status: Mapped[str] = mapped_column(String, default="none", index=True)

    price_cents: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String, default="BRL")
    interval: Mapped[str] = mapped_column(String, default="monthly")

    locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    granted_at: Mapped[float | None] = mapped_column(Float, nullable=True)

    credited_until: Mapped[float | None] = mapped_column(Float, nullable=True)
    credited_days_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    trial_started_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    trial_ends_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_period_end: Mapped[float | None] = mapped_column(Float, nullable=True)
    cancelled_at: Mapped[float | None] = mapped_column(Float, nullable=True)

    provider: Mapped[str] = mapped_column(String, default="none")
    external_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    created_at: Mapped[float] = mapped_column(Float, default=time.time)
    updated_at: Mapped[float] = mapped_column(Float, default=time.time)


class ProcessedWebhookDb(Base):
    __tablename__ = "processed_webhooks"

    provider: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    processed_at: Mapped[float] = mapped_column(Float)
    summary: Mapped[str] = mapped_column(String, default="")


class ReferralCodeDb(Base):
    __tablename__ = "referral_codes"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_at: Mapped[float] = mapped_column(Float, default=time.time)


class ReferralDb(Base):
    __tablename__ = "referrals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    referred_user_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    code: Mapped[str] = mapped_column(String, index=True)

    created_at: Mapped[float] = mapped_column(Float, default=time.time)
    qualified_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    rewarded_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    reward_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
