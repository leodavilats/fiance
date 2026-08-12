from __future__ import annotations

import time
from contextlib import contextmanager
from datetime import UTC
from typing import TypedDict

from sqlalchemy import delete, func, select

from app.core.context import get_current_user_id
from app.core.database import SessionLocal, init_db
from app.models.db_models import (
    ClosedTradeDb,
    DeviceTokenDb,
    GoalDb,
    NotifiedOpportunityDb,
    PortfolioPosition,
    PortfolioSnapshot,
    PreferencesDb,
    PriceAlertDb,
    SectorGoalDb,
    User,
    WatchlistItemDb,
)

DEFAULT_USER = "default"

_initialized = False


class StoredItem(TypedDict):
    ticker: str
    quantity: float
    avg_price: float
    category: str
    updated_at: float


class Snapshot(TypedDict):
    captured_at: float
    total_invested: float
    total_current: float
    total_pnl: float
    total_pnl_pct: float


class Goal(TypedDict):
    category: str
    target_pct: float
    target_value: float | None
    deadline: str | None


class SectorGoal(TypedDict):
    sector: str
    target_pct: float


class Preferences(TypedDict):
    cash_available: float
    passive_income_goal: float | None
    desired_yield_stock: float
    desired_yield_fii: float
    desired_yield_int: float
    notify_price_alerts: bool
    notify_new_opportunities: bool
    updated_at: float


class DeviceToken(TypedDict):
    id: int
    user_id: str
    token: str
    platform: str


class WatchlistItemRow(TypedDict):
    ticker: str
    note: str
    created_at: float


class PriceAlert(TypedDict):
    id: int
    ticker: str
    condition: str
    target_price: float
    note: str | None
    created_at: float
    triggered_at: float | None


class ClosedTrade(TypedDict):
    id: int
    ticker: str
    category: str
    quantity: float
    avg_price: float
    sell_price: float
    gross_profit: float
    ir_rate: float
    ir_amount: float
    net_profit: float
    sold_at: float


def _ensure_user(session, user_id: str) -> None:
    if session.get(User, user_id) is None:
        session.merge(User(id=user_id, email=f"{user_id}@local", name=user_id))


@contextmanager
def _session(user_id: str | None):
    global _initialized
    if not _initialized:
        init_db()
        _initialized = True

    uid = user_id or get_current_user_id()
    session = SessionLocal()
    try:
        _ensure_user(session, uid)
        yield session, uid
        session.commit()
    finally:
        session.close()


def list_positions(user_id: str | None = None) -> list[StoredItem]:
    with _session(user_id) as (session, uid):
        rows = session.scalars(
            select(PortfolioPosition)
            .where(PortfolioPosition.user_id == uid)
            .order_by(PortfolioPosition.ticker)
        ).all()
        return [
            StoredItem(
                ticker=r.ticker,
                quantity=r.quantity,
                avg_price=r.avg_price,
                category=r.category or "auto",
                updated_at=r.updated_at,
            )
            for r in rows
        ]


def upsert_position(
    ticker: str,
    quantity: float,
    avg_price: float,
    category: str = "auto",
    user_id: str | None = None,
) -> None:
    now = time.time()
    t = ticker.strip().upper()
    with _session(user_id) as (session, uid):
        row = session.get(PortfolioPosition, (uid, t))
        if row is None:
            row = PortfolioPosition(
                user_id=uid,
                ticker=t,
                quantity=quantity,
                avg_price=avg_price,
                category=category,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
        else:
            row.quantity = quantity
            row.avg_price = avg_price
            row.category = category
            row.updated_at = now


def update_category(ticker: str, category: str, user_id: str | None = None) -> None:
    with _session(user_id) as (session, uid):
        row = session.get(PortfolioPosition, (uid, ticker.strip().upper()))
        if row is not None:
            row.category = category
            row.updated_at = time.time()


def replace_all(items: list[StoredItem], user_id: str | None = None) -> None:
    validated = [
        it for it in items if it.get("ticker") and it.get("quantity") and it.get("avg_price")
    ]
    if not validated:
        return

    now = time.time()
    with _session(user_id) as (session, uid):
        session.execute(delete(PortfolioPosition).where(PortfolioPosition.user_id == uid))
        for it in validated:
            session.add(
                PortfolioPosition(
                    user_id=uid,
                    ticker=it["ticker"].upper(),
                    quantity=float(it["quantity"]),
                    avg_price=float(it["avg_price"]),
                    category=it.get("category", "auto") or "auto",
                    created_at=now,
                    updated_at=now,
                )
            )


def delete_position(ticker: str, user_id: str | None = None) -> None:
    with _session(user_id) as (session, uid):
        session.execute(
            delete(PortfolioPosition).where(
                PortfolioPosition.user_id == uid,
                PortfolioPosition.ticker == ticker.strip().upper(),
            )
        )


def get_position(ticker: str, user_id: str | None = None) -> StoredItem | None:
    with _session(user_id) as (session, uid):
        row = session.get(PortfolioPosition, (uid, ticker.strip().upper()))
        if row is None:
            return None
        return StoredItem(
            ticker=row.ticker,
            quantity=row.quantity,
            avg_price=row.avg_price,
            category=row.category or "auto",
            updated_at=row.updated_at,
        )


def reduce_position_quantity(ticker: str, sold_qty: float, user_id: str | None = None) -> None:
    t = ticker.strip().upper()
    with _session(user_id) as (session, uid):
        row = session.get(PortfolioPosition, (uid, t))
        if row is None:
            return
        remaining = row.quantity - sold_qty
        if remaining <= 1e-9:
            session.execute(
                delete(PortfolioPosition).where(
                    PortfolioPosition.user_id == uid, PortfolioPosition.ticker == t
                )
            )
        else:
            row.quantity = remaining
            row.updated_at = time.time()


def sum_gross_sales_this_month(ticker_category: str, user_id: str | None = None) -> float:
    # usado para aplicar a isenção mensal de IR (R$20k ações BR / R$35k cripto) sobre o acumulado do mês
    now = time.time()
    from datetime import datetime

    dt = datetime.fromtimestamp(now, tz=UTC)
    month_start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0).timestamp()

    with _session(user_id) as (session, uid):
        rows = session.scalars(
            select(ClosedTradeDb).where(
                ClosedTradeDb.user_id == uid,
                ClosedTradeDb.category == ticker_category,
                ClosedTradeDb.sold_at >= month_start,
            )
        ).all()
        return sum(r.quantity * r.sell_price for r in rows)


def create_closed_trade(
    ticker: str,
    category: str,
    quantity: float,
    avg_price: float,
    sell_price: float,
    gross_profit: float,
    ir_rate: float,
    ir_amount: float,
    net_profit: float,
    sold_at: float,
    user_id: str | None = None,
) -> ClosedTrade:
    now = time.time()
    with _session(user_id) as (session, uid):
        row = ClosedTradeDb(
            user_id=uid,
            ticker=ticker.strip().upper(),
            category=category,
            quantity=quantity,
            avg_price=avg_price,
            sell_price=sell_price,
            gross_profit=gross_profit,
            ir_rate=ir_rate,
            ir_amount=ir_amount,
            net_profit=net_profit,
            sold_at=sold_at,
            created_at=now,
        )
        session.add(row)
        session.flush()
        return ClosedTrade(
            id=row.id or 0,
            ticker=row.ticker,
            category=row.category,
            quantity=row.quantity,
            avg_price=row.avg_price,
            sell_price=row.sell_price,
            gross_profit=row.gross_profit,
            ir_rate=row.ir_rate,
            ir_amount=row.ir_amount,
            net_profit=row.net_profit,
            sold_at=row.sold_at,
        )


def list_closed_trades(user_id: str | None = None) -> list[ClosedTrade]:
    with _session(user_id) as (session, uid):
        rows = session.scalars(
            select(ClosedTradeDb)
            .where(ClosedTradeDb.user_id == uid)
            .order_by(ClosedTradeDb.sold_at.desc())
        ).all()
        return [
            ClosedTrade(
                id=r.id,
                ticker=r.ticker,
                category=r.category,
                quantity=r.quantity,
                avg_price=r.avg_price,
                sell_price=r.sell_price,
                gross_profit=r.gross_profit,
                ir_rate=r.ir_rate,
                ir_amount=r.ir_amount,
                net_profit=r.net_profit,
                sold_at=r.sold_at,
            )
            for r in rows
        ]


def record_snapshot(
    total_invested: float,
    total_current: float,
    total_pnl: float,
    total_pnl_pct: float,
    user_id: str | None = None,
) -> None:
    now = time.time()
    day_key = int(now // 86400) * 86400
    cutoff = now - (365 * 86400)

    with _session(user_id) as (session, uid):
        row = session.get(PortfolioSnapshot, (uid, day_key))
        if row is None:
            session.add(
                PortfolioSnapshot(
                    user_id=uid,
                    captured_at=day_key,
                    total_invested=total_invested,
                    total_current=total_current,
                    total_pnl=total_pnl,
                    total_pnl_pct=total_pnl_pct,
                )
            )
        else:
            row.total_invested = total_invested
            row.total_current = total_current
            row.total_pnl = total_pnl
            row.total_pnl_pct = total_pnl_pct

        session.execute(
            delete(PortfolioSnapshot).where(
                PortfolioSnapshot.user_id == uid,
                PortfolioSnapshot.captured_at < cutoff,
            )
        )


def list_snapshots(limit: int = 90, user_id: str | None = None) -> list[Snapshot]:
    with _session(user_id) as (session, uid):
        rows = session.scalars(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.user_id == uid)
            .order_by(PortfolioSnapshot.captured_at.desc())
            .limit(limit)
        ).all()
        return [
            Snapshot(
                captured_at=r.captured_at,
                total_invested=r.total_invested,
                total_current=r.total_current,
                total_pnl=r.total_pnl,
                total_pnl_pct=r.total_pnl_pct,
            )
            for r in reversed(rows)
        ]


def last_updated(user_id: str | None = None) -> float | None:
    with _session(user_id) as (session, uid):
        return session.scalar(
            select(func.max(PortfolioPosition.updated_at)).where(PortfolioPosition.user_id == uid)
        )


def list_goals(user_id: str | None = None) -> list[Goal]:
    with _session(user_id) as (session, uid):
        rows = session.scalars(
            select(GoalDb).where(GoalDb.user_id == uid).order_by(GoalDb.category)
        ).all()
        return [
            Goal(
                category=r.category,
                target_pct=r.target_pct,
                target_value=r.target_value,
                deadline=r.deadline,
            )
            for r in rows
        ]


def replace_goals(goals: list[Goal], user_id: str | None = None) -> None:
    with _session(user_id) as (session, uid):
        session.execute(delete(GoalDb).where(GoalDb.user_id == uid))
        for g in goals:
            session.add(
                GoalDb(
                    user_id=uid,
                    category=g["category"],
                    target_pct=float(g["target_pct"]),
                    target_value=g.get("target_value"),
                    deadline=g.get("deadline"),
                )
            )


def get_preferences(user_id: str | None = None) -> Preferences:
    with _session(user_id) as (session, uid):
        row = session.get(PreferencesDb, uid)
        if row:
            return Preferences(
                cash_available=row.cash_available,
                passive_income_goal=row.passive_income_goal,
                desired_yield_stock=row.desired_yield_stock,
                desired_yield_fii=row.desired_yield_fii,
                desired_yield_int=row.desired_yield_int,
                notify_price_alerts=row.notify_price_alerts,
                notify_new_opportunities=row.notify_new_opportunities,
                updated_at=row.updated_at,
            )

    return Preferences(
        cash_available=0.0,
        passive_income_goal=None,
        desired_yield_stock=0.06,
        desired_yield_fii=0.10,
        desired_yield_int=0.04,
        notify_price_alerts=True,
        notify_new_opportunities=True,
        updated_at=0.0,
    )


def set_preferences(
    cash_available: float,
    passive_income_goal: float | None = None,
    desired_yield_stock: float | None = None,
    desired_yield_fii: float | None = None,
    desired_yield_int: float | None = None,
    notify_price_alerts: bool | None = None,
    notify_new_opportunities: bool | None = None,
    user_id: str | None = None,
) -> None:
    now = time.time()
    with _session(user_id) as (session, uid):
        row = session.get(PreferencesDb, uid)
        if row is None:
            row = PreferencesDb(
                user_id=uid,
                cash_available=float(cash_available),
                passive_income_goal=passive_income_goal,
                desired_yield_stock=desired_yield_stock
                if desired_yield_stock is not None
                else 0.06,
                desired_yield_fii=desired_yield_fii if desired_yield_fii is not None else 0.10,
                desired_yield_int=desired_yield_int if desired_yield_int is not None else 0.04,
                notify_price_alerts=notify_price_alerts
                if notify_price_alerts is not None
                else True,
                notify_new_opportunities=notify_new_opportunities
                if notify_new_opportunities is not None
                else True,
                updated_at=now,
            )
            session.add(row)
        else:
            row.cash_available = float(cash_available)
            row.passive_income_goal = passive_income_goal
            if desired_yield_stock is not None:
                row.desired_yield_stock = desired_yield_stock
            if desired_yield_fii is not None:
                row.desired_yield_fii = desired_yield_fii
            if desired_yield_int is not None:
                row.desired_yield_int = desired_yield_int
            if notify_price_alerts is not None:
                row.notify_price_alerts = notify_price_alerts
            if notify_new_opportunities is not None:
                row.notify_new_opportunities = notify_new_opportunities
            row.updated_at = now


def register_device_token(
    token: str, platform: str = "android", user_id: str | None = None
) -> None:
    # reatribui o token ao usuário atual mesmo se já pertencia a outro (troca de conta no mesmo aparelho)
    with _session(user_id) as (session, uid):
        existing = session.scalar(select(DeviceTokenDb).where(DeviceTokenDb.token == token))
        if existing is not None:
            existing.user_id = uid
            existing.platform = platform
        else:
            session.add(
                DeviceTokenDb(user_id=uid, token=token, platform=platform, created_at=time.time())
            )


def unregister_device_token(token: str, user_id: str | None = None) -> None:
    with _session(user_id) as (session, uid):
        session.execute(
            delete(DeviceTokenDb).where(DeviceTokenDb.user_id == uid, DeviceTokenDb.token == token)
        )


def list_all_device_tokens() -> list[DeviceToken]:
    with _session(DEFAULT_USER) as (session, _uid):
        rows = session.scalars(select(DeviceTokenDb)).all()
        return [
            DeviceToken(id=r.id, user_id=r.user_id, token=r.token, platform=r.platform)
            for r in rows
        ]


def list_device_tokens(user_id: str | None = None) -> list[DeviceToken]:
    with _session(user_id) as (session, uid):
        rows = session.scalars(select(DeviceTokenDb).where(DeviceTokenDb.user_id == uid)).all()
        return [
            DeviceToken(id=r.id, user_id=r.user_id, token=r.token, platform=r.platform)
            for r in rows
        ]


def get_notified_opportunity_tickers(user_id: str) -> set[str]:
    with _session(user_id) as (session, uid):
        rows = session.scalars(
            select(NotifiedOpportunityDb.ticker).where(NotifiedOpportunityDb.user_id == uid)
        ).all()
        return set(rows)


def mark_opportunities_notified(user_id: str, tickers: list[str]) -> None:
    now = time.time()
    with _session(user_id) as (session, uid):
        for ticker in tickers:
            if session.get(NotifiedOpportunityDb, (uid, ticker)) is None:
                session.add(NotifiedOpportunityDb(user_id=uid, ticker=ticker, notified_at=now))


def list_sector_goals(user_id: str | None = None) -> list[SectorGoal]:
    with _session(user_id) as (session, uid):
        rows = session.scalars(
            select(SectorGoalDb).where(SectorGoalDb.user_id == uid).order_by(SectorGoalDb.sector)
        ).all()
        return [SectorGoal(sector=r.sector, target_pct=r.target_pct) for r in rows]


def replace_sector_goals(goals: list[SectorGoal], user_id: str | None = None) -> None:
    with _session(user_id) as (session, uid):
        session.execute(delete(SectorGoalDb).where(SectorGoalDb.user_id == uid))
        for g in goals:
            session.add(
                SectorGoalDb(user_id=uid, sector=g["sector"], target_pct=float(g["target_pct"]))
            )


def list_watchlist(user_id: str | None = None) -> list[WatchlistItemRow]:
    with _session(user_id) as (session, uid):
        rows = session.scalars(
            select(WatchlistItemDb)
            .where(WatchlistItemDb.user_id == uid)
            .order_by(WatchlistItemDb.created_at.desc())
        ).all()
        return [
            WatchlistItemRow(ticker=r.ticker, note=r.note or "", created_at=r.created_at)
            for r in rows
        ]


def replace_watchlist(items: list[dict], user_id: str | None = None) -> None:
    now = time.time()
    with _session(user_id) as (session, uid):
        session.execute(delete(WatchlistItemDb).where(WatchlistItemDb.user_id == uid))
        for it in items:
            ticker = str(it.get("ticker", "")).strip().upper()
            if not ticker:
                continue
            session.add(
                WatchlistItemDb(
                    user_id=uid, ticker=ticker, note=it.get("note") or "", created_at=now
                )
            )


def remove_watchlist(ticker: str, user_id: str | None = None) -> None:
    with _session(user_id) as (session, uid):
        session.execute(
            delete(WatchlistItemDb).where(
                WatchlistItemDb.user_id == uid,
                WatchlistItemDb.ticker == ticker.strip().upper(),
            )
        )


def list_price_alerts(user_id: str | None = None) -> list[PriceAlert]:
    with _session(user_id) as (session, uid):
        rows = session.scalars(
            select(PriceAlertDb)
            .where(PriceAlertDb.user_id == uid)
            .order_by(PriceAlertDb.created_at.desc())
        ).all()
        return [
            PriceAlert(
                id=r.id,
                ticker=r.ticker,
                condition=r.condition,
                target_price=r.target_price,
                note=r.note,
                created_at=r.created_at,
                triggered_at=r.triggered_at,
            )
            for r in rows
        ]


def create_price_alert(
    ticker: str,
    condition: str,
    target_price: float,
    note: str | None = None,
    user_id: str | None = None,
) -> int:
    now = time.time()
    with _session(user_id) as (session, uid):
        row = PriceAlertDb(
            user_id=uid,
            ticker=ticker.strip().upper(),
            condition=condition,
            target_price=float(target_price),
            note=note,
            created_at=now,
        )
        session.add(row)
        session.flush()
        return row.id or 0


def delete_price_alert(alert_id: int, user_id: str | None = None) -> bool:
    with _session(user_id) as (session, uid):
        result = session.execute(
            delete(PriceAlertDb).where(PriceAlertDb.id == alert_id, PriceAlertDb.user_id == uid)
        )
        return result.rowcount > 0


def mark_alert_triggered(alert_id: int, user_id: str | None = None) -> None:
    with _session(user_id) as (session, uid):
        row = session.get(PriceAlertDb, alert_id)
        if row is not None and row.user_id == uid:
            row.triggered_at = time.time()
