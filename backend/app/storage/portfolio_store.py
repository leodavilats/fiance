from __future__ import annotations

import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TypedDict

DB_PATH = Path(__file__).resolve().parent.parent.parent / ".cache" / "portfolio.db"

DEFAULT_USER = "default"


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


class WatchlistItem(TypedDict):
    ticker: str

    note: str

    created_at: float


class Goal(TypedDict):
    category: str

    target_pct: float

    target_value: float | None

    deadline: str | None


class Preferences(TypedDict):
    cash_available: float

    desired_yield: float

    updated_at: float


def _init() -> None:

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as cx:
        cx.executescript(
            """
            CREATE TABLE IF NOT EXISTS portfolio (
                user_id    TEXT NOT NULL,
                ticker     TEXT NOT NULL,
                quantity   REAL NOT NULL,
                avg_price  REAL NOT NULL,
                category   TEXT NOT NULL DEFAULT 'auto',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                PRIMARY KEY (user_id, ticker)
            );

            CREATE TABLE IF NOT EXISTS portfolio_snapshot (
                user_id          TEXT NOT NULL,
                captured_at      REAL NOT NULL,
                total_invested   REAL NOT NULL,
                total_current    REAL NOT NULL,
                total_pnl        REAL NOT NULL,
                total_pnl_pct    REAL NOT NULL,
                PRIMARY KEY (user_id, captured_at)
            );

            CREATE TABLE IF NOT EXISTS watchlist (
                user_id    TEXT NOT NULL,
                ticker     TEXT NOT NULL,
                note       TEXT DEFAULT '',
                created_at REAL NOT NULL,
                PRIMARY KEY (user_id, ticker)
            );

            CREATE TABLE IF NOT EXISTS goals (
                user_id      TEXT NOT NULL,
                category     TEXT NOT NULL,
                target_pct   REAL NOT NULL,
                target_value REAL,
                deadline     TEXT,
                PRIMARY KEY (user_id, category)
            );

            CREATE TABLE IF NOT EXISTS preferences (
                user_id        TEXT PRIMARY KEY,
                cash_available REAL NOT NULL DEFAULT 0,
                desired_yield  REAL NOT NULL DEFAULT 0.06,
                updated_at     REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_snap_user ON portfolio_snapshot(user_id, captured_at);
            """
        )

        try:
            cx.execute("ALTER TABLE goals ADD COLUMN target_value REAL")

        except sqlite3.OperationalError:
            pass

        try:
            cx.execute("ALTER TABLE goals ADD COLUMN deadline TEXT")

        except sqlite3.OperationalError:
            pass

        try:
            cx.execute("ALTER TABLE portfolio ADD COLUMN category TEXT NOT NULL DEFAULT 'auto'")

        except sqlite3.OperationalError:
            pass


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:

    _init()

    cx = sqlite3.connect(DB_PATH)

    cx.row_factory = sqlite3.Row

    try:
        yield cx

        cx.commit()

    finally:
        cx.close()


def list_positions(user_id: str = DEFAULT_USER) -> list[StoredItem]:

    with _conn() as cx:
        rows = cx.execute(
            "SELECT ticker, quantity, avg_price, category, updated_at "
            "FROM portfolio WHERE user_id = ? ORDER BY ticker",
            (user_id,),
        ).fetchall()

    return [
        StoredItem(
            ticker=r["ticker"],
            quantity=r["quantity"],
            avg_price=r["avg_price"],
            category=r["category"] or "auto",
            updated_at=r["updated_at"],
        )
        for r in rows
    ]


def upsert_position(
    ticker: str,
    quantity: float,
    avg_price: float,
    category: str = "auto",
    user_id: str = DEFAULT_USER,
) -> None:

    now = time.time()

    t = ticker.strip().upper()

    with _conn() as cx:
        cx.execute(
            """
            INSERT INTO portfolio(user_id, ticker, quantity, avg_price, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, ticker) DO UPDATE SET
                quantity   = excluded.quantity,
                avg_price  = excluded.avg_price,
                category   = excluded.category,
                updated_at = excluded.updated_at
            """,
            (user_id, t, quantity, avg_price, category, now, now),
        )


def update_category(ticker: str, category: str, user_id: str = DEFAULT_USER) -> None:

    with _conn() as cx:
        cx.execute(
            "UPDATE portfolio SET category = ?, updated_at = ? WHERE user_id = ? AND ticker = ?",
            (category, time.time(), user_id, ticker.strip().upper()),
        )


def replace_all(
    items: list[StoredItem],
    user_id: str = DEFAULT_USER,
) -> None:

    now = time.time()

    with _conn() as cx:
        cx.execute("DELETE FROM portfolio WHERE user_id = ?", (user_id,))

        cx.executemany(
            """
            INSERT INTO portfolio(user_id, ticker, quantity, avg_price, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    user_id,
                    it["ticker"].upper(),
                    float(it["quantity"]),
                    float(it["avg_price"]),
                    it.get("category", "auto") or "auto",
                    now,
                    now,
                )
                for it in items
                if it.get("ticker") and it.get("quantity") and it.get("avg_price")
            ],
        )


def delete_position(ticker: str, user_id: str = DEFAULT_USER) -> None:

    with _conn() as cx:
        cx.execute(
            "DELETE FROM portfolio WHERE user_id = ? AND ticker = ?",
            (user_id, ticker.strip().upper()),
        )


def record_snapshot(
    total_invested: float,
    total_current: float,
    total_pnl: float,
    total_pnl_pct: float,
    user_id: str = DEFAULT_USER,
) -> None:

    now = time.time()

    day_key = int(now // 86400) * 86400

    with _conn() as cx:
        cx.execute(
            """
            INSERT INTO portfolio_snapshot(
                user_id, captured_at, total_invested, total_current, total_pnl, total_pnl_pct
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, captured_at) DO UPDATE SET
                total_invested = excluded.total_invested,
                total_current  = excluded.total_current,
                total_pnl      = excluded.total_pnl,
                total_pnl_pct  = excluded.total_pnl_pct
            """,
            (user_id, day_key, total_invested, total_current, total_pnl, total_pnl_pct),
        )


def list_snapshots(limit: int = 90, user_id: str = DEFAULT_USER) -> list[Snapshot]:

    with _conn() as cx:
        rows = cx.execute(
            "SELECT captured_at, total_invested, total_current, total_pnl, total_pnl_pct "
            "FROM portfolio_snapshot WHERE user_id = ? "
            "ORDER BY captured_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()

    return [
        Snapshot(
            captured_at=r["captured_at"],
            total_invested=r["total_invested"],
            total_current=r["total_current"],
            total_pnl=r["total_pnl"],
            total_pnl_pct=r["total_pnl_pct"],
        )
        for r in reversed(rows)
    ]


def last_updated(user_id: str = DEFAULT_USER) -> float | None:

    with _conn() as cx:
        row = cx.execute(
            "SELECT MAX(updated_at) AS u FROM portfolio WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    return row["u"] if row and row["u"] else None


def list_watchlist(user_id: str = DEFAULT_USER) -> list[WatchlistItem]:

    with _conn() as cx:
        rows = cx.execute(
            "SELECT ticker, note, created_at FROM watchlist WHERE user_id = ? ORDER BY ticker",
            (user_id,),
        ).fetchall()

    return [
        WatchlistItem(ticker=r["ticker"], note=r["note"] or "", created_at=r["created_at"])
        for r in rows
    ]


def add_watchlist(ticker: str, note: str = "", user_id: str = DEFAULT_USER) -> None:

    with _conn() as cx:
        cx.execute(
            """
            INSERT INTO watchlist(user_id, ticker, note, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, ticker) DO UPDATE SET note = excluded.note
            """,
            (user_id, ticker.strip().upper(), note, time.time()),
        )


def remove_watchlist(ticker: str, user_id: str = DEFAULT_USER) -> None:

    with _conn() as cx:
        cx.execute(
            "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?",
            (user_id, ticker.strip().upper()),
        )


def replace_watchlist(items: list[WatchlistItem], user_id: str = DEFAULT_USER) -> None:

    now = time.time()

    with _conn() as cx:
        cx.execute("DELETE FROM watchlist WHERE user_id = ?", (user_id,))

        cx.executemany(
            "INSERT INTO watchlist(user_id, ticker, note, created_at) VALUES (?, ?, ?, ?)",
            [
                (user_id, it["ticker"].upper(), it.get("note", ""), now)
                for it in items
                if it.get("ticker")
            ],
        )


def list_goals(user_id: str = DEFAULT_USER) -> list[Goal]:

    with _conn() as cx:
        rows = cx.execute(
            "SELECT category, target_pct, target_value, deadline FROM goals WHERE user_id = ? ORDER BY category",
            (user_id,),
        ).fetchall()

    return [
        Goal(
            category=r["category"],
            target_pct=r["target_pct"],
            target_value=r["target_value"],
            deadline=r["deadline"],
        )
        for r in rows
    ]


def replace_goals(goals: list[Goal], user_id: str = DEFAULT_USER) -> None:

    with _conn() as cx:
        cx.execute("DELETE FROM goals WHERE user_id = ?", (user_id,))

        cx.executemany(
            "INSERT INTO goals(user_id, category, target_pct, target_value, deadline) VALUES (?, ?, ?, ?, ?)",
            [
                (
                    user_id,
                    g["category"],
                    float(g["target_pct"]),
                    g.get("target_value"),
                    g.get("deadline"),
                )
                for g in goals
            ],
        )


def get_preferences(user_id: str = DEFAULT_USER) -> Preferences:

    with _conn() as cx:
        row = cx.execute(
            "SELECT cash_available, desired_yield, updated_at FROM preferences WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    if row:
        return Preferences(
            cash_available=row["cash_available"],
            desired_yield=row["desired_yield"],
            updated_at=row["updated_at"],
        )

    return Preferences(cash_available=0.0, desired_yield=0.06, updated_at=0.0)


def set_preferences(
    cash_available: float,
    desired_yield: float = 0.06,
    user_id: str = DEFAULT_USER,
) -> None:

    now = time.time()

    with _conn() as cx:
        cx.execute(
            """
            INSERT INTO preferences(user_id, cash_available, desired_yield, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                cash_available = excluded.cash_available,
                desired_yield  = excluded.desired_yield,
                updated_at     = excluded.updated_at
            """,
            (user_id, float(cash_available), float(desired_yield), now),
        )
