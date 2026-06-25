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

            CREATE TABLE IF NOT EXISTS sector_goals (
                user_id    TEXT NOT NULL,
                sector     TEXT NOT NULL,
                target_pct REAL NOT NULL,
                PRIMARY KEY (user_id, sector)
            );

            CREATE TABLE IF NOT EXISTS preferences (
                user_id        TEXT PRIMARY KEY,
                cash_available REAL NOT NULL DEFAULT 0,
                desired_yield  REAL NOT NULL DEFAULT 0.06,
                updated_at     REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS price_alerts (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      TEXT NOT NULL,
                ticker       TEXT NOT NULL,
                condition    TEXT NOT NULL CHECK(condition IN ('above','below')),
                target_price REAL NOT NULL,
                note         TEXT,
                created_at   REAL NOT NULL,
                triggered_at REAL
            );

            CREATE INDEX IF NOT EXISTS idx_snap_user ON portfolio_snapshot(user_id, captured_at);
            CREATE INDEX IF NOT EXISTS idx_alerts_user ON price_alerts(user_id);
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

        try:
            cx.execute("ALTER TABLE preferences ADD COLUMN passive_income_goal REAL")

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

    validated = [
        it for it in items if it.get("ticker") and it.get("quantity") and it.get("avg_price")
    ]

    if not validated:
        return

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
                for it in validated
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

    cutoff = now - (365 * 86400)

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
        cx.execute(
            "DELETE FROM portfolio_snapshot WHERE user_id = ? AND captured_at < ?",
            (user_id, cutoff),
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
            "SELECT cash_available, passive_income_goal, updated_at FROM preferences WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    if row:
        return Preferences(
            cash_available=row["cash_available"],
            passive_income_goal=row["passive_income_goal"],
            updated_at=row["updated_at"],
        )

    return Preferences(cash_available=0.0, passive_income_goal=None, updated_at=0.0)


def set_preferences(
    cash_available: float,
    passive_income_goal: float | None = None,
    user_id: str = DEFAULT_USER,
) -> None:

    now = time.time()

    with _conn() as cx:
        cx.execute(
            """
            INSERT INTO preferences(user_id, cash_available, passive_income_goal, desired_yield, updated_at)
            VALUES (?, ?, ?, 0.06, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                cash_available       = excluded.cash_available,
                passive_income_goal  = excluded.passive_income_goal,
                updated_at           = excluded.updated_at
            """,
            (user_id, float(cash_available), passive_income_goal, now),
        )


def list_sector_goals(user_id: str = DEFAULT_USER) -> list[SectorGoal]:
    with _conn() as cx:
        rows = cx.execute(
            "SELECT sector, target_pct FROM sector_goals WHERE user_id = ? ORDER BY sector",
            (user_id,),
        ).fetchall()

    return [
        SectorGoal(
            sector=r["sector"],
            target_pct=r["target_pct"],
        )
        for r in rows
    ]


def replace_sector_goals(goals: list[SectorGoal], user_id: str = DEFAULT_USER) -> None:
    with _conn() as cx:
        cx.execute("DELETE FROM sector_goals WHERE user_id = ?", (user_id,))

        cx.executemany(
            "INSERT INTO sector_goals(user_id, sector, target_pct) VALUES (?, ?, ?)",
            [(user_id, g["sector"], float(g["target_pct"])) for g in goals],
        )


class PriceAlert(TypedDict):
    id: int
    ticker: str
    condition: str
    target_price: float
    note: str | None
    created_at: float
    triggered_at: float | None


def list_price_alerts(user_id: str = DEFAULT_USER) -> list[PriceAlert]:
    with _conn() as cx:
        rows = cx.execute(
            "SELECT id, ticker, condition, target_price, note, created_at, triggered_at "
            "FROM price_alerts WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
    return [
        PriceAlert(
            id=r["id"],
            ticker=r["ticker"],
            condition=r["condition"],
            target_price=r["target_price"],
            note=r["note"],
            created_at=r["created_at"],
            triggered_at=r["triggered_at"],
        )
        for r in rows
    ]


def create_price_alert(
    ticker: str,
    condition: str,
    target_price: float,
    note: str | None = None,
    user_id: str = DEFAULT_USER,
) -> int:
    now = time.time()
    with _conn() as cx:
        cur = cx.execute(
            "INSERT INTO price_alerts(user_id, ticker, condition, target_price, note, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, ticker.strip().upper(), condition, float(target_price), note, now),
        )
        return cur.lastrowid or 0


def delete_price_alert(alert_id: int, user_id: str = DEFAULT_USER) -> bool:
    with _conn() as cx:
        cur = cx.execute(
            "DELETE FROM price_alerts WHERE id = ? AND user_id = ?",
            (alert_id, user_id),
        )
        return cur.rowcount > 0


def mark_alert_triggered(alert_id: int, user_id: str = DEFAULT_USER) -> None:
    with _conn() as cx:
        cx.execute(
            "UPDATE price_alerts SET triggered_at = ? WHERE id = ? AND user_id = ?",
            (time.time(), alert_id, user_id),
        )
