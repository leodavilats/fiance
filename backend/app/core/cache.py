from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent.parent / ".cache" / "fianceai.db"


def _ensure_db() -> None:

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as cx:
        cx.execute(
            "CREATE TABLE IF NOT EXISTS cache ("
            "  k TEXT PRIMARY KEY,"
            "  v TEXT NOT NULL,"
            "  expires_at REAL NOT NULL"
            ")"
        )


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:

    _ensure_db()

    cx = sqlite3.connect(DB_PATH)

    try:
        yield cx

        cx.commit()

    finally:
        cx.close()


def get(key: str) -> Any | None:

    with _conn() as cx:
        row = cx.execute("SELECT v, expires_at FROM cache WHERE k = ?", (key,)).fetchone()

    if not row:
        return None

    value, expires_at = row

    if expires_at < time.time():
        delete(key)

        return None

    try:
        return json.loads(value)

    except json.JSONDecodeError:
        return None


def set(key: str, value: Any, ttl_seconds: int) -> None:

    with _conn() as cx:
        cx.execute(
            "INSERT OR REPLACE INTO cache(k, v, expires_at) VALUES (?, ?, ?)",
            (key, json.dumps(value, default=str), time.time() + ttl_seconds),
        )


def delete(key: str) -> None:

    with _conn() as cx:
        cx.execute("DELETE FROM cache WHERE k = ?", (key,))


def delete_pattern(pattern: str) -> int:
    with _conn() as cx:
        cursor = cx.execute("DELETE FROM cache WHERE k LIKE ?", (pattern,))
        return cursor.rowcount


def clear_all() -> int:
    with _conn() as cx:
        cursor = cx.execute("DELETE FROM cache")
        return cursor.rowcount
