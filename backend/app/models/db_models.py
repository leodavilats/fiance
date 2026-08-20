from __future__ import annotations

import time

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String, default="")
    picture: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[float] = mapped_column(Float, default=time.time)


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
    # Quanto de prejuízo acumulado foi consumido por esta venda. Persistido (em
    # vez de recalculado) para que o saldo de compensação seja auditável e não
    # mude retroativamente quando a regra evoluir.
    loss_offset_used: Mapped[float] = mapped_column(Float, default=0.0)
    taxable_profit: Mapped[float] = mapped_column(Float, default=0.0)
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
    """Renda fixa como entidade de primeira classe.

    Antes taxa, prazo, data de aplicação e % do CDI viviam só no localStorage
    do navegador e o servidor só conhecia o valor investido, num ticker
    sintético RF_<tipo>_<índice>. Consequências diretas: trocar de navegador
    zerava os rendimentos, o mobile nunca via os detalhes, o patrimônio total
    subestimava sistematicamente e não havia como alertar vencimento próximo
    porque a data de vencimento não existia em lugar nenhum do servidor.
    """

    __tablename__ = "fixed_income_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    nome: Mapped[str] = mapped_column(String)
    tipo: Mapped[str] = mapped_column(String)
    valor_investido: Mapped[float] = mapped_column(Float)
    taxa: Mapped[float] = mapped_column(Float)
    tipo_taxa: Mapped[str] = mapped_column(String, default="pre_fixado")
    percentual_cdi: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Datas em ISO (YYYY-MM-DD): comparáveis por string e portáveis entre
    # SQLite e Postgres sem depender do dialeto de DATE.
    data_aplicacao: Mapped[str] = mapped_column(String)
    vencimento: Mapped[str | None] = mapped_column(String, nullable=True)
    liquidez: Mapped[str] = mapped_column(String, default="no_vencimento")
    isento_ir: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    oculto: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[float] = mapped_column(Float)


class JobLockDb(Base):
    """Lock cooperativo para jobs de background.

    Os dois `asyncio.create_task` do startup rodavam em todo worker: com mais
    de um dyno/worker, cada um executava o ciclo de notificação — pushes
    duplicados para o mesmo usuário. Um lock no banco (que é compartilhado) é o
    mínimo para tornar os jobs idempotentes entre processos.
    """

    __tablename__ = "job_locks"

    name: Mapped[str] = mapped_column(String, primary_key=True)
    holder: Mapped[str] = mapped_column(String)
    acquired_at: Mapped[float] = mapped_column(Float)
    expires_at: Mapped[float] = mapped_column(Float)


class DividendReceivedDb(Base):
    """Provento efetivamente creditado.

    Todo número de renda no produto era estimativa derivada de DY; o histórico
    real de proventos não existia em tabela nenhuma, então "quanto eu recebi
    este mês" não tinha resposta.
    """

    __tablename__ = "dividends_received"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    ticker: Mapped[str] = mapped_column(String, index=True)
    # Data em ISO (YYYY-MM-DD): comparável por string e portável entre SQLite e
    # Postgres sem depender do dialeto de DATE.
    paid_at: Mapped[str] = mapped_column(String, index=True)
    amount: Mapped[float] = mapped_column(Float)
    kind: Mapped[str] = mapped_column(String, default="dividendo")
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[float] = mapped_column(Float)


class FollowedSuggestionDb(Base):
    """Sugestão que o usuário declarou ter seguido.

    Fechava-se metade do ciclo: o produto sugeria e nunca sabia o que aconteceu
    depois. Com isto, o resultado das sugestões fica auditável pelo próprio
    usuário — histórico verificável em vez de argumento de autoridade.
    """

    __tablename__ = "followed_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    ticker: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[str] = mapped_column(String, default="opportunities")
    action: Mapped[str] = mapped_column(String, default="comprar")
    quantity: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    # ISO YYYY-MM-DD, comparável por string e portável entre dialetos.
    followed_on: Mapped[str] = mapped_column(String, index=True)
    score_at_suggestion: Mapped[float | None] = mapped_column(Float, nullable=True)
    verdict_at_suggestion: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[float] = mapped_column(Float)
