from __future__ import annotations

import time
from contextlib import contextmanager
from decimal import Decimal
from typing import TypedDict

from sqlalchemy import delete, func, select

from app.core.brt import month_bounds
from app.core.context import get_current_user_id, get_request_session
from app.core.database import SessionLocal, init_db
from app.core.money import ZERO, money, quantize, sum_money, to_float
from app.core.pagination import apply_keyset
from app.models.db_models import (
    ClosedTradeDb,
    DeviceTokenDb,
    DividendReceivedDb,
    FixedIncomePositionDb,
    FollowedSuggestionDb,
    GoalDb,
    JobLockDb,
    NotifiedOpportunityDb,
    PortfolioPosition,
    PortfolioSnapshot,
    PreferencesDb,
    PriceAlertDb,
    SectorGoalDb,
    User,
)

_initialized = False


def _list_to_csv(items: list[str] | None) -> str:
    return ",".join(items) if items else ""


def _csv_to_list(csv: str | None) -> list[str]:
    return [v for v in (csv or "").split(",") if v]


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
    desired_yield_bdr: float
    desired_yield_etf: float
    notify_price_alerts: bool
    opportunities_frequency: str
    risk_profile: str
    density: str
    preferred_categories: list[str]
    preferred_sectors: list[str]
    excluded_tickers: list[str]
    updated_at: float


class DeviceToken(TypedDict):
    id: int
    user_id: str
    token: str
    platform: str


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
    loss_offset_used: float
    taxable_profit: float
    loss_compensable: bool
    sold_at: float


def _ensure_user(session, user_id: str) -> None:
    if session.get(User, user_id) is None:
        session.merge(User(id=user_id, email=f"{user_id}@local", name=user_id))


def ensure_user(session, user_id: str) -> None:
    _ensure_user(session, user_id)
    session.flush()


@contextmanager
def _session(user_id: str | None, ensure_user: bool = False):
    global _initialized
    if not _initialized:
        init_db()
        _initialized = True

    uid = user_id or get_current_user_id()

    ambient = get_request_session()
    if ambient is not None:
        if ensure_user:
            _ensure_user(ambient, uid)
        yield ambient, uid
        ambient.flush()
        return

    session = SessionLocal()
    try:
        if ensure_user:
            _ensure_user(session, uid)
        yield session, uid
        session.commit()
    finally:
        session.close()


@contextmanager
def _session_global():
    global _initialized
    if not _initialized:
        init_db()
        _initialized = True

    session = SessionLocal()
    try:
        yield session
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
                quantity=to_float(r.quantity),
                avg_price=to_float(r.avg_price),
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
    with _session(user_id, ensure_user=True) as (session, uid):
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
            row.quantity = money(quantity)
            row.avg_price = money(avg_price)
            row.category = category
            row.updated_at = now


def update_category(ticker: str, category: str, user_id: str | None = None) -> None:
    with _session(user_id, ensure_user=True) as (session, uid):
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
    with _session(user_id, ensure_user=True) as (session, uid):
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
            quantity=to_float(row.quantity),
            avg_price=to_float(row.avg_price),
            category=row.category or "auto",
            updated_at=row.updated_at,
        )


def reduce_position_quantity(ticker: str, sold_qty: float, user_id: str | None = None) -> None:
    t = ticker.strip().upper()
    with _session(user_id) as (session, uid):
        row = session.get(PortfolioPosition, (uid, t))
        if row is None:
            return
        remaining = row.quantity - money(sold_qty)
        if remaining <= 1e-9:
            session.execute(
                delete(PortfolioPosition).where(
                    PortfolioPosition.user_id == uid, PortfolioPosition.ticker == t
                )
            )
        else:
            row.quantity = remaining
            row.updated_at = time.time()


def realized_gross_profit_between(start: float, end: float, user_id: str | None = None) -> float:
    with _session(user_id) as (session, uid):
        lucros = session.scalars(
            select(ClosedTradeDb.gross_profit).where(
                ClosedTradeDb.user_id == uid,
                ClosedTradeDb.sold_at >= start,
                ClosedTradeDb.sold_at < end,
            )
        ).all()
        return to_float(sum_money(lucros))


def lock_tenant(user_id: str | None = None) -> None:
    with _session(user_id, ensure_user=True) as (session, uid):
        stmt = select(User).where(User.id == uid)
        if session.bind is not None and session.bind.dialect.name != "sqlite":
            stmt = stmt.with_for_update()
        session.scalars(stmt).first()


def sum_gross_sales_in_month(
    ticker_category: str, at: float | None = None, user_id: str | None = None
) -> float:
    month_start, month_end = month_bounds(at)

    with _session(user_id) as (session, uid):
        rows = session.scalars(
            select(ClosedTradeDb).where(
                ClosedTradeDb.user_id == uid,
                ClosedTradeDb.category == ticker_category,
                ClosedTradeDb.sold_at >= month_start,
                ClosedTradeDb.sold_at < month_end,
            )
        ).all()
        return to_float(sum_money(r.quantity * r.sell_price for r in rows))


def sum_gross_sales_this_month(ticker_category: str, user_id: str | None = None) -> float:
    return sum_gross_sales_in_month(ticker_category, at=None, user_id=user_id)


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
    loss_offset_used: float = 0.0,
    taxable_profit: float = 0.0,
    loss_compensable: bool = True,
    user_id: str | None = None,
) -> ClosedTrade:
    now = time.time()
    with _session(user_id, ensure_user=True) as (session, uid):
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
            loss_offset_used=loss_offset_used,
            taxable_profit=taxable_profit,
            loss_compensable=loss_compensable,
            sold_at=sold_at,
            created_at=now,
        )
        session.add(row)
        session.flush()
        return ClosedTrade(
            id=row.id or 0,
            ticker=row.ticker,
            category=row.category,
            quantity=to_float(row.quantity),
            avg_price=to_float(row.avg_price),
            sell_price=to_float(row.sell_price),
            gross_profit=to_float(row.gross_profit),
            ir_rate=row.ir_rate,
            ir_amount=to_float(row.ir_amount),
            net_profit=to_float(row.net_profit),
            loss_offset_used=to_float(row.loss_offset_used or 0.0),
            taxable_profit=to_float(row.taxable_profit or 0.0),
            loss_compensable=bool(row.loss_compensable),
            sold_at=row.sold_at,
        )


def list_closed_trades(
    user_id: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> list[ClosedTrade]:
    with _session(user_id) as (session, uid):
        stmt = apply_keyset(
            select(ClosedTradeDb).where(ClosedTradeDb.user_id == uid),
            ClosedTradeDb.sold_at,
            ClosedTradeDb.id,
            cursor,
        )
        if limit is not None:
            stmt = stmt.limit(limit + 1)
        rows = session.scalars(stmt).all()
        return [
            ClosedTrade(
                id=r.id,
                ticker=r.ticker,
                category=r.category,
                quantity=to_float(r.quantity),
                avg_price=to_float(r.avg_price),
                sell_price=to_float(r.sell_price),
                gross_profit=to_float(r.gross_profit),
                ir_rate=r.ir_rate,
                ir_amount=to_float(r.ir_amount),
                net_profit=to_float(r.net_profit),
                loss_offset_used=to_float(r.loss_offset_used or 0.0),
                taxable_profit=to_float(r.taxable_profit or 0.0),
                loss_compensable=bool(r.loss_compensable),
                sold_at=r.sold_at,
            )
            for r in rows
        ]


def closed_trades_totals(user_id: str | None = None) -> dict:
    with _session(user_id) as (session, uid):
        linhas = session.execute(
            select(ClosedTradeDb.net_profit, ClosedTradeDb.ir_amount).where(
                ClosedTradeDb.user_id == uid
            )
        ).all()
        row = (
            sum_money(linha[0] for linha in linhas),
            sum_money(linha[1] for linha in linhas),
            len(linhas),
        )

        return {
            "total_realized_pnl": float(row[0] or 0.0),
            "total_ir_paid": float(row[1] or 0.0),
            "count": int(row[2] or 0),
        }


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

    with _session(user_id, ensure_user=True) as (session, uid):
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
                total_invested=to_float(r.total_invested),
                total_current=to_float(r.total_current),
                total_pnl=to_float(r.total_pnl),
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
                target_value=to_float(r.target_value) if r.target_value is not None else None,
                deadline=r.deadline,
            )
            for r in rows
        ]


def replace_goals(goals: list[Goal], user_id: str | None = None) -> None:
    with _session(user_id, ensure_user=True) as (session, uid):
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
                cash_available=to_float(row.cash_available),
                passive_income_goal=(
                    to_float(row.passive_income_goal)
                    if row.passive_income_goal is not None
                    else None
                ),
                desired_yield_stock=row.desired_yield_stock,
                desired_yield_fii=row.desired_yield_fii,
                desired_yield_bdr=row.desired_yield_bdr,
                desired_yield_etf=row.desired_yield_etf,
                notify_price_alerts=row.notify_price_alerts,
                opportunities_frequency=row.opportunities_frequency,
                risk_profile=row.risk_profile,
                density=row.density or "comfortable",
                preferred_categories=_csv_to_list(row.preferred_categories),
                preferred_sectors=_csv_to_list(row.preferred_sectors),
                excluded_tickers=_csv_to_list(row.excluded_tickers),
                updated_at=row.updated_at,
            )

    return Preferences(
        cash_available=0.0,
        passive_income_goal=None,
        desired_yield_stock=0.06,
        desired_yield_fii=0.10,
        desired_yield_bdr=0.04,
        desired_yield_etf=0.04,
        notify_price_alerts=True,
        opportunities_frequency="weekly",
        risk_profile="moderate",
        density="comfortable",
        preferred_categories=[],
        preferred_sectors=[],
        excluded_tickers=[],
        updated_at=0.0,
    )


_PREF_DEFAULTS: dict[str, object] = {
    "cash_available": 0.0,
    "passive_income_goal": None,
    "desired_yield_stock": 0.06,
    "desired_yield_fii": 0.10,
    "desired_yield_bdr": 0.04,
    "desired_yield_etf": 0.04,
    "notify_price_alerts": True,
    "opportunities_frequency": "weekly",
    "risk_profile": "moderate",
    "density": "comfortable",
    "preferred_categories": [],
    "preferred_sectors": [],
    "excluded_tickers": [],
}

_PREF_CSV_FIELDS = {"preferred_categories", "preferred_sectors", "excluded_tickers"}

_PREF_ANULAVEIS = {"passive_income_goal"}


def set_preferences(user_id: str | None = None, **fields) -> None:
    unknown = set(fields) - set(_PREF_DEFAULTS)
    if unknown:
        raise ValueError(f"Campos de preferência desconhecidos: {sorted(unknown)}")

    fields = {k: v for k, v in fields.items() if v is not None or k in _PREF_ANULAVEIS}

    now = time.time()
    with _session(user_id, ensure_user=True) as (session, uid):
        row = session.get(PreferencesDb, uid)
        if row is None:
            values = dict(_PREF_DEFAULTS)
            values.update(fields)
            row = PreferencesDb(
                user_id=uid,
                updated_at=now,
                **{k: (_list_to_csv(v) if k in _PREF_CSV_FIELDS else v) for k, v in values.items()},
            )
            session.add(row)
        else:
            for k, v in fields.items():
                setattr(row, k, _list_to_csv(v) if k in _PREF_CSV_FIELDS else v)
            row.updated_at = now


def get_last_digest_sent_at(user_id: str | None = None) -> float | None:
    with _session(user_id) as (session, uid):
        row = session.get(PreferencesDb, uid)
        return row.last_digest_sent_at if row else None


def mark_digest_sent(sent_at: float, user_id: str | None = None) -> None:
    with _session(user_id, ensure_user=True) as (session, uid):
        row = session.get(PreferencesDb, uid)
        if row is None:
            row = PreferencesDb(user_id=uid, last_digest_sent_at=sent_at, updated_at=sent_at)
            session.add(row)
        else:
            row.last_digest_sent_at = sent_at


def register_device_token(
    token: str, platform: str = "android", user_id: str | None = None
) -> None:
    with _session(user_id, ensure_user=True) as (session, uid):
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
    with _session_global() as session:
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
    with _session(user_id, ensure_user=True) as (session, uid):
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
    with _session(user_id, ensure_user=True) as (session, uid):
        session.execute(delete(SectorGoalDb).where(SectorGoalDb.user_id == uid))
        for g in goals:
            session.add(
                SectorGoalDb(user_id=uid, sector=g["sector"], target_pct=float(g["target_pct"]))
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
                target_price=to_float(r.target_price),
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
    with _session(user_id, ensure_user=True) as (session, uid):
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


class FixedIncomeRow(TypedDict):
    id: int
    nome: str
    tipo: str
    valor_investido: float
    taxa: float
    tipo_taxa: str
    percentual_cdi: float | None
    data_aplicacao: str
    vencimento: str | None
    liquidez: str
    isento_ir: bool | None
    oculto: bool
    created_at: float
    updated_at: float


_FIXED_INCOME_FIELDS = (
    "nome",
    "tipo",
    "valor_investido",
    "taxa",
    "tipo_taxa",
    "percentual_cdi",
    "data_aplicacao",
    "vencimento",
    "liquidez",
    "isento_ir",
    "oculto",
)


def _fixed_income_row(row: FixedIncomePositionDb) -> FixedIncomeRow:
    return FixedIncomeRow(
        id=row.id,
        nome=row.nome,
        tipo=row.tipo,
        valor_investido=to_float(row.valor_investido),
        taxa=row.taxa,
        tipo_taxa=row.tipo_taxa,
        percentual_cdi=row.percentual_cdi,
        data_aplicacao=row.data_aplicacao,
        vencimento=row.vencimento,
        liquidez=row.liquidez,
        isento_ir=row.isento_ir,
        oculto=bool(row.oculto),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def has_holdings(user_id: str | None = None) -> bool:
    with _session(user_id) as (session, uid):
        tem_variavel = session.scalar(
            select(PortfolioPosition.ticker).where(PortfolioPosition.user_id == uid).limit(1)
        )
        if tem_variavel is not None:
            return True

        tem_fixa = session.scalar(
            select(FixedIncomePositionDb.id).where(FixedIncomePositionDb.user_id == uid).limit(1)
        )
        return tem_fixa is not None


def list_fixed_income(
    user_id: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> list[FixedIncomeRow]:
    with _session(user_id) as (session, uid):
        stmt = apply_keyset(
            select(FixedIncomePositionDb).where(FixedIncomePositionDb.user_id == uid),
            FixedIncomePositionDb.data_aplicacao,
            FixedIncomePositionDb.id,
            cursor,
        )
        if limit is not None:
            stmt = stmt.limit(limit + 1)
        return [_fixed_income_row(r) for r in session.scalars(stmt).all()]


def get_fixed_income(position_id: int, user_id: str | None = None) -> FixedIncomeRow | None:
    with _session(user_id) as (session, uid):
        row = session.get(FixedIncomePositionDb, position_id)
        if row is None or row.user_id != uid:
            return None
        return _fixed_income_row(row)


def create_fixed_income(user_id: str | None = None, **fields) -> FixedIncomeRow:
    unknown = set(fields) - set(_FIXED_INCOME_FIELDS)
    if unknown:
        raise ValueError(f"Campos de renda fixa desconhecidos: {sorted(unknown)}")

    now = time.time()
    with _session(user_id, ensure_user=True) as (session, uid):
        row = FixedIncomePositionDb(user_id=uid, created_at=now, updated_at=now, **fields)
        session.add(row)
        session.flush()
        return _fixed_income_row(row)


def update_fixed_income(
    position_id: int, user_id: str | None = None, **fields
) -> FixedIncomeRow | None:
    unknown = set(fields) - set(_FIXED_INCOME_FIELDS)
    if unknown:
        raise ValueError(f"Campos de renda fixa desconhecidos: {sorted(unknown)}")

    with _session(user_id) as (session, uid):
        row = session.get(FixedIncomePositionDb, position_id)
        if row is None or row.user_id != uid:
            return None
        for key, value in fields.items():
            setattr(row, key, value)
        row.updated_at = time.time()
        session.flush()
        return _fixed_income_row(row)


def delete_fixed_income(position_id: int, user_id: str | None = None) -> bool:
    with _session(user_id) as (session, uid):
        result = session.execute(
            delete(FixedIncomePositionDb).where(
                FixedIncomePositionDb.id == position_id,
                FixedIncomePositionDb.user_id == uid,
            )
        )
        return result.rowcount > 0


def purge_legacy_fixed_income_tickers() -> int:
    with _session_global() as session:
        result = session.execute(
            delete(PortfolioPosition).where(PortfolioPosition.ticker.like("RF!_%", escape="!"))
        )
        return result.rowcount or 0


def list_all_user_ids() -> list[str]:
    with _session_global() as session:
        return list(session.scalars(select(User.id)))


def try_acquire_job_lock(name: str, holder: str, ttl_seconds: float) -> bool:
    now = time.time()
    with _session_global() as session:
        row = session.get(JobLockDb, name)
        if row is None:
            session.add(
                JobLockDb(name=name, holder=holder, acquired_at=now, expires_at=now + ttl_seconds)
            )
            return True

        if row.expires_at > now and row.holder != holder:
            return False

        row.holder = holder
        row.acquired_at = now
        row.expires_at = now + ttl_seconds
        return True


def release_job_lock(name: str, holder: str) -> None:
    with _session_global() as session:
        row = session.get(JobLockDb, name)
        if row is not None and row.holder == holder:
            session.execute(delete(JobLockDb).where(JobLockDb.name == name))


class TaxLossBalance(TypedDict):
    category: str
    realized_loss: float
    offset_used: float
    available: float


def tax_loss_balances(user_id: str | None = None) -> list[TaxLossBalance]:
    by_category: dict[str, dict[str, Decimal]] = {}

    with _session(user_id) as (session, uid):
        rows = session.execute(
            select(
                ClosedTradeDb.category,
                ClosedTradeDb.gross_profit,
                ClosedTradeDb.loss_offset_used,
                ClosedTradeDb.loss_compensable,
            ).where(ClosedTradeDb.user_id == uid)
        ).all()

        for category, gross_profit, offset_used, compensable in rows:
            bucket = by_category.setdefault(category, {"realized_loss": ZERO, "offset_used": ZERO})
            if gross_profit < 0 and compensable:
                bucket["realized_loss"] += abs(money(gross_profit))
            bucket["offset_used"] += money(offset_used or 0)

    return [
        TaxLossBalance(
            category=category,
            realized_loss=to_float(quantize(values["realized_loss"])),
            offset_used=to_float(quantize(values["offset_used"])),
            available=to_float(
                quantize(max(values["realized_loss"] - values["offset_used"], ZERO))
            ),
        )
        for category, values in sorted(by_category.items())
    ]


def available_tax_loss(category: str, user_id: str | None = None) -> float:
    for balance in tax_loss_balances(user_id=user_id):
        if balance["category"] == category:
            return balance["available"]
    return 0.0


class DividendReceivedRow(TypedDict):
    id: int
    ticker: str
    paid_at: str
    amount: float
    kind: str
    note: str | None


_DIVIDEND_FIELDS = ("ticker", "paid_at", "amount", "kind", "note")


def _dividend_row(row: DividendReceivedDb) -> DividendReceivedRow:
    return DividendReceivedRow(
        id=row.id,
        ticker=row.ticker,
        paid_at=row.paid_at,
        amount=to_float(row.amount),
        kind=row.kind,
        note=row.note,
    )


def list_dividends_received(
    user_id: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> list[DividendReceivedRow]:
    with _session(user_id) as (session, uid):
        stmt = apply_keyset(
            select(DividendReceivedDb).where(DividendReceivedDb.user_id == uid),
            DividendReceivedDb.paid_at,
            DividendReceivedDb.id,
            cursor,
        )
        if limit is not None:
            stmt = stmt.limit(limit + 1)
        return [_dividend_row(r) for r in session.scalars(stmt).all()]


def create_dividend_received(user_id: str | None = None, **fields) -> DividendReceivedRow:
    unknown = set(fields) - set(_DIVIDEND_FIELDS)
    if unknown:
        raise ValueError(f"Campos de provento desconhecidos: {sorted(unknown)}")

    now = time.time()
    with _session(user_id, ensure_user=True) as (session, uid):
        row = DividendReceivedDb(user_id=uid, created_at=now, updated_at=now, **fields)
        session.add(row)
        session.flush()
        return _dividend_row(row)


def update_dividend_received(
    dividend_id: int, user_id: str | None = None, **fields
) -> DividendReceivedRow | None:
    unknown = set(fields) - set(_DIVIDEND_FIELDS)
    if unknown:
        raise ValueError(f"Campos de provento desconhecidos: {sorted(unknown)}")

    with _session(user_id) as (session, uid):
        row = session.get(DividendReceivedDb, dividend_id)
        if row is None or row.user_id != uid:
            return None
        for key, value in fields.items():
            setattr(row, key, value)
        row.updated_at = time.time()
        session.flush()
        return _dividend_row(row)


def delete_dividend_received(dividend_id: int, user_id: str | None = None) -> bool:
    with _session(user_id) as (session, uid):
        result = session.execute(
            delete(DividendReceivedDb).where(
                DividendReceivedDb.id == dividend_id,
                DividendReceivedDb.user_id == uid,
            )
        )
        return result.rowcount > 0


class FollowedSuggestionRow(TypedDict):
    id: int
    ticker: str
    source: str
    action: str
    quantity: float
    price: float
    followed_on: str
    score_at_suggestion: float | None
    verdict_at_suggestion: str | None
    note: str | None


_FOLLOWED_FIELDS = (
    "ticker",
    "source",
    "action",
    "quantity",
    "price",
    "followed_on",
    "score_at_suggestion",
    "verdict_at_suggestion",
    "note",
)


def _followed_row(row: FollowedSuggestionDb) -> FollowedSuggestionRow:
    return FollowedSuggestionRow(
        id=row.id,
        ticker=row.ticker,
        source=row.source,
        action=row.action,
        quantity=to_float(row.quantity),
        price=to_float(row.price),
        followed_on=row.followed_on,
        score_at_suggestion=row.score_at_suggestion,
        verdict_at_suggestion=row.verdict_at_suggestion,
        note=row.note,
    )


def list_followed_suggestions(
    user_id: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> list[FollowedSuggestionRow]:
    with _session(user_id) as (session, uid):
        stmt = apply_keyset(
            select(FollowedSuggestionDb).where(FollowedSuggestionDb.user_id == uid),
            FollowedSuggestionDb.followed_on,
            FollowedSuggestionDb.id,
            cursor,
        )
        if limit is not None:
            stmt = stmt.limit(limit + 1)
        return [_followed_row(r) for r in session.scalars(stmt).all()]


def create_followed_suggestion(user_id: str | None = None, **fields) -> FollowedSuggestionRow:
    unknown = set(fields) - set(_FOLLOWED_FIELDS)
    if unknown:
        raise ValueError(f"Campos de sugestão seguida desconhecidos: {sorted(unknown)}")

    with _session(user_id, ensure_user=True) as (session, uid):
        row = FollowedSuggestionDb(user_id=uid, created_at=time.time(), **fields)
        session.add(row)
        session.flush()
        return _followed_row(row)


def delete_followed_suggestion(suggestion_id: int, user_id: str | None = None) -> bool:
    with _session(user_id) as (session, uid):
        result = session.execute(
            delete(FollowedSuggestionDb).where(
                FollowedSuggestionDb.id == suggestion_id,
                FollowedSuggestionDb.user_id == uid,
            )
        )
        return result.rowcount > 0
