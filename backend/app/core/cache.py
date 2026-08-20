from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

logger = logging.getLogger("fiance.cache")

# Arquivo **dedicado** ao cache. Antes DB_PATH resolvia para
# `backend/.cache/fiance.db` — o mesmo arquivo do `database_url` default em
# desenvolvimento. Com 30 threads de coleta (_FETCH_SEMAPHORE) escrevendo cache
# nele, o churn travava as escritas de dado do usuário com "database is
# locked". Sobrescrevível por CACHE_DB_PATH.
_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / ".cache" / "http_cache.db"
DB_PATH = Path(os.environ.get("CACHE_DB_PATH") or _DEFAULT_DB_PATH)

# Uma conexão por thread, reaproveitada: abrir/fechar por operação custava um
# handshake de arquivo em cada get/set, e um scan completo faz milhares deles.
_local = threading.local()
_init_lock = threading.Lock()
_initialized = False

_BUSY_TIMEOUT_MS = 5_000


def _record_lookup(hit: bool) -> None:
    # Import tardio: observability importa database, que importa config —
    # importar no topo criaria ciclo com quem usa cache no import.
    try:
        from app.core.observability import record_cache_lookup

        record_cache_lookup(hit)
    except Exception:
        pass


def _ensure_db() -> None:
    global _initialized
    if _initialized:
        return

    with _init_lock:
        if _initialized:
            return
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(DB_PATH) as cx:
            # WAL: leitores não bloqueiam o escritor nem vice-versa — é o que
            # torna o cache utilizável sob concorrência.
            cx.execute("PRAGMA journal_mode=WAL")
            cx.execute("PRAGMA synchronous=NORMAL")
            cx.execute(
                "CREATE TABLE IF NOT EXISTS cache ("
                "  k TEXT PRIMARY KEY,"
                "  v TEXT NOT NULL,"
                "  expires_at REAL NOT NULL"
                ")"
            )
            cx.execute("CREATE INDEX IF NOT EXISTS ix_cache_expires ON cache(expires_at)")
        _initialized = True


def _connection() -> sqlite3.Connection:
    _ensure_db()

    cx = getattr(_local, "cx", None)
    if cx is None:
        cx = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)
        cx.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
        cx.execute("PRAGMA journal_mode=WAL")
        cx.execute("PRAGMA synchronous=NORMAL")
        _local.cx = cx
    return cx


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    cx = _connection()
    try:
        yield cx
    except sqlite3.Error:
        # Conexão possivelmente inutilizável: descarta para a próxima chamada
        # reabrir em vez de reusar um handle quebrado.
        _local.cx = None
        try:
            cx.close()
        except sqlite3.Error:
            pass
        raise


def reset_connection() -> None:
    """Fecha a conexão desta thread (usado em testes e após trocar DB_PATH)."""
    cx = getattr(_local, "cx", None)
    if cx is not None:
        try:
            cx.close()
        except sqlite3.Error:
            pass
        _local.cx = None


def get(key: str) -> Any | None:
    try:
        with _conn() as cx:
            row = cx.execute("SELECT v, expires_at FROM cache WHERE k = ?", (key,)).fetchone()
    except sqlite3.Error as exc:
        logger.warning("Falha ao ler cache %s: %s", key, exc)
        return None

    if not row:
        _record_lookup(hit=False)
        return None

    value, expires_at = row

    if expires_at < time.time():
        _record_lookup(hit=False)
        delete(key)
        return None

    _record_lookup(hit=True)
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def get_with_age(key: str) -> tuple[Any | None, float | None]:
    """Valor e segundos desde o vencimento, **mesmo vencido**.

    É o que permite servir stale-while-revalidate: devolver o último scan
    conhecido na hora e recalcular em background, em vez de fazer o usuário
    pagar o scan do universo inteiro dentro do request.

    Retorna `(valor, segundos_de_atraso)`. `segundos_de_atraso` é 0 quando o
    valor ainda está fresco e `None` quando não há valor nenhum.
    """
    try:
        with _conn() as cx:
            row = cx.execute("SELECT v, expires_at FROM cache WHERE k = ?", (key,)).fetchone()
    except sqlite3.Error as exc:
        logger.warning("Falha ao ler cache %s: %s", key, exc)
        return None, None

    if not row:
        return None, None

    value, expires_at = row
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None, None

    return parsed, max(0.0, time.time() - expires_at)


def set(key: str, value: Any, ttl_seconds: int) -> None:
    try:
        with _conn() as cx:
            cx.execute(
                "INSERT OR REPLACE INTO cache(k, v, expires_at) VALUES (?, ?, ?)",
                (key, json.dumps(value, default=str), time.time() + ttl_seconds),
            )
    except sqlite3.Error as exc:
        # Cache indisponível degrada performance, não corretude — nunca deve
        # derrubar o request.
        logger.warning("Falha ao gravar cache %s: %s", key, exc)


def delete(key: str) -> None:
    try:
        with _conn() as cx:
            cx.execute("DELETE FROM cache WHERE k = ?", (key,))
    except sqlite3.Error as exc:
        logger.warning("Falha ao apagar cache %s: %s", key, exc)


def delete_pattern(pattern: str) -> int:
    with _conn() as cx:
        cursor = cx.execute("DELETE FROM cache WHERE k LIKE ?", (pattern,))
        return cursor.rowcount


def clear_all() -> int:
    with _conn() as cx:
        cursor = cx.execute("DELETE FROM cache")
        return cursor.rowcount


def purge_expired() -> int:
    """Remove entradas vencidas. Chamado pelo ciclo de manutenção."""
    with _conn() as cx:
        cursor = cx.execute("DELETE FROM cache WHERE expires_at < ?", (time.time(),))
        return cursor.rowcount
