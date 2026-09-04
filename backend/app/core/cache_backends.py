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
from typing import Any, Protocol

logger = logging.getLogger("fiance.cache")

STALE_MARGIN_SECONDS = 6 * 3600


class CacheBackend(Protocol):
    name: str
    shared: bool

    def get_raw(self, key: str) -> tuple[str, float] | None: ...

    def set_raw(self, key: str, payload: str, expires_at: float) -> None: ...

    def delete(self, key: str) -> None: ...

    def delete_pattern(self, pattern: str) -> int: ...

    def clear_all(self) -> int: ...

    def purge_expired(self) -> int: ...


_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / ".cache" / "http_cache.db"
DB_PATH = Path(os.environ.get("CACHE_DB_PATH") or _DEFAULT_DB_PATH)


class SqliteBackend:
    name = "sqlite"
    shared = False

    _BUSY_TIMEOUT_MS = 5_000

    def __init__(self) -> None:
        self._local = threading.local()
        self._init_lock = threading.Lock()
        self._initialized = False
        self._path = DB_PATH

    def _ensure_db(self) -> None:
        if self._initialized and self._path == DB_PATH:
            return

        with self._init_lock:
            if self._initialized and self._path == DB_PATH:
                return
            self._path = DB_PATH
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(DB_PATH) as cx:
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
            self._initialized = True

    def _connection(self) -> sqlite3.Connection:
        self._ensure_db()

        cx = getattr(self._local, "cx", None)
        if cx is None:
            cx = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)
            cx.execute(f"PRAGMA busy_timeout={self._BUSY_TIMEOUT_MS}")
            cx.execute("PRAGMA journal_mode=WAL")
            cx.execute("PRAGMA synchronous=NORMAL")
            self._local.cx = cx
        return cx

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        cx = self._connection()
        try:
            yield cx
        except sqlite3.Error:
            self._local.cx = None
            try:
                cx.close()
            except sqlite3.Error:
                pass
            raise

    def reset_connection(self) -> None:
        cx = getattr(self._local, "cx", None)
        if cx is not None:
            try:
                cx.close()
            except sqlite3.Error:
                pass
            self._local.cx = None
        self._initialized = False

    def get_raw(self, key: str) -> tuple[str, float] | None:
        try:
            with self._conn() as cx:
                row = cx.execute("SELECT v, expires_at FROM cache WHERE k = ?", (key,)).fetchone()
        except sqlite3.Error as exc:
            logger.warning("Falha ao ler cache %s: %s", key, exc)
            return None
        return (row[0], row[1]) if row else None

    def set_raw(self, key: str, payload: str, expires_at: float) -> None:
        try:
            with self._conn() as cx:
                cx.execute(
                    "INSERT OR REPLACE INTO cache(k, v, expires_at) VALUES (?, ?, ?)",
                    (key, payload, expires_at),
                )
        except sqlite3.Error as exc:
            logger.warning("Falha ao gravar cache %s: %s", key, exc)

    def delete(self, key: str) -> None:
        try:
            with self._conn() as cx:
                cx.execute("DELETE FROM cache WHERE k = ?", (key,))
        except sqlite3.Error as exc:
            logger.warning("Falha ao apagar cache %s: %s", key, exc)

    def delete_pattern(self, pattern: str) -> int:
        with self._conn() as cx:
            return cx.execute("DELETE FROM cache WHERE k LIKE ?", (pattern,)).rowcount

    def clear_all(self) -> int:
        with self._conn() as cx:
            return cx.execute("DELETE FROM cache").rowcount

    def purge_expired(self) -> int:
        with self._conn() as cx:
            return cx.execute("DELETE FROM cache WHERE expires_at < ?", (time.time(),)).rowcount


class RedisBackend:
    name = "redis"
    shared = True

    def __init__(self, url: str, prefix: str = "fiance:cache:", client: Any = None) -> None:
        self._prefix = prefix

        if client is not None:
            self._client = client
            return

        try:
            import redis  # noqa: PLC0415
        except ModuleNotFoundError as exc:  # pragma: no cover - depende do ambiente
            raise RuntimeError(
                "REDIS_URL está configurado mas o pacote `redis` não está instalado. "
                "Sem ele o cache voltaria a ser por nó, e nós diferentes mostrariam "
                "preços diferentes para a mesma pessoa — falhar aqui é melhor do que "
                "descobrir isso em produção."
            ) from exc

        self._client = redis.Redis.from_url(url, decode_responses=True)

    def _k(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def get_raw(self, key: str) -> tuple[str, float] | None:
        try:
            bruto = self._client.get(self._k(key))
        except Exception as exc:  # pragma: no cover - depende de servidor
            logger.warning("Falha ao ler cache %s: %s", key, exc)
            return None

        if not bruto:
            return None
        try:
            envelope = json.loads(bruto)
            return envelope["v"], float(envelope["e"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None

    def set_raw(self, key: str, payload: str, expires_at: float) -> None:
        envelope = json.dumps({"v": payload, "e": expires_at})
        sobrevida = max(1, int(expires_at - time.time()) + STALE_MARGIN_SECONDS)
        try:
            self._client.set(self._k(key), envelope, ex=sobrevida)
        except Exception as exc:  # pragma: no cover - depende de servidor
            logger.warning("Falha ao gravar cache %s: %s", key, exc)

    def delete(self, key: str) -> None:
        try:
            self._client.delete(self._k(key))
        except Exception as exc:  # pragma: no cover - depende de servidor
            logger.warning("Falha ao apagar cache %s: %s", key, exc)

    def _scan(self, match: str) -> list[str]:
        return list(self._client.scan_iter(match=match, count=500))

    def delete_pattern(self, pattern: str) -> int:
        glob = self._prefix + pattern.replace("%", "*")
        chaves = self._scan(glob)
        return int(self._client.delete(*chaves)) if chaves else 0

    def clear_all(self) -> int:
        chaves = self._scan(f"{self._prefix}*")
        return int(self._client.delete(*chaves)) if chaves else 0

    def purge_expired(self) -> int:
        return 0


class DatabaseBackend:
    name = "database"

    def __init__(self) -> None:
        self._pronto = False
        self._lock = threading.Lock()

    def _ensure_db(self) -> None:
        if self._pronto:
            return
        with self._lock:
            if self._pronto:
                return
            from app.core.database import ensure_initialized  # noqa: PLC0415

            ensure_initialized()
            self._pronto = True

    @contextmanager
    def _session(self) -> Iterator[Any]:
        self._ensure_db()
        from app.core.database import SessionLocal  # noqa: PLC0415

        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @property
    def shared(self) -> bool:
        return _url_do_banco_e_compartilhada()

    def get_raw(self, key: str) -> tuple[str, float] | None:
        from sqlalchemy import select  # noqa: PLC0415

        from app.models.db_models import CacheEntryDb  # noqa: PLC0415

        try:
            with self._session() as session:
                row = session.execute(
                    select(CacheEntryDb.v, CacheEntryDb.expires_at).where(CacheEntryDb.k == key)
                ).first()
        except Exception as exc:
            logger.warning("Falha ao ler cache %s: %s", key, exc)
            return None

        return (row[0], float(row[1])) if row else None

    def set_raw(self, key: str, payload: str, expires_at: float) -> None:
        from app.models.db_models import CacheEntryDb  # noqa: PLC0415

        try:
            with self._session() as session:
                dialeto = session.bind.dialect.name
                if dialeto == "postgresql":
                    from sqlalchemy.dialects.postgresql import insert  # noqa: PLC0415
                elif dialeto == "sqlite":
                    from sqlalchemy.dialects.sqlite import insert  # noqa: PLC0415
                else:
                    insert = None

                if insert is None:
                    session.query(CacheEntryDb).filter(CacheEntryDb.k == key).delete()
                    session.add(CacheEntryDb(k=key, v=payload, expires_at=expires_at))
                    return

                comando = insert(CacheEntryDb).values(k=key, v=payload, expires_at=expires_at)
                session.execute(
                    comando.on_conflict_do_update(
                        index_elements=[CacheEntryDb.k],
                        set_={"v": payload, "expires_at": expires_at},
                    )
                )
        except Exception as exc:
            logger.warning("Falha ao gravar cache %s: %s", key, exc)

    def delete(self, key: str) -> None:
        from app.models.db_models import CacheEntryDb  # noqa: PLC0415

        try:
            with self._session() as session:
                session.query(CacheEntryDb).filter(CacheEntryDb.k == key).delete()
        except Exception as exc:
            logger.warning("Falha ao apagar cache %s: %s", key, exc)

    def delete_pattern(self, pattern: str) -> int:
        from app.models.db_models import CacheEntryDb  # noqa: PLC0415

        try:
            with self._session() as session:
                return int(
                    session.query(CacheEntryDb)
                    .filter(CacheEntryDb.k.like(pattern))
                    .delete(synchronize_session=False)
                )
        except Exception as exc:
            logger.warning("Falha ao apagar cache por padrão %s: %s", pattern, exc)
            return 0

    def clear_all(self) -> int:
        from app.models.db_models import CacheEntryDb  # noqa: PLC0415

        try:
            with self._session() as session:
                return int(session.query(CacheEntryDb).delete(synchronize_session=False))
        except Exception as exc:
            logger.warning("Falha ao limpar cache: %s", exc)
            return 0

    def purge_expired(self) -> int:
        from app.models.db_models import CacheEntryDb  # noqa: PLC0415

        try:
            with self._session() as session:
                return int(
                    session.query(CacheEntryDb)
                    .filter(CacheEntryDb.expires_at < time.time())
                    .delete(synchronize_session=False)
                )
        except Exception as exc:
            logger.warning("Falha ao purgar cache: %s", exc)
            return 0


BACKENDS_CONHECIDOS = ("sqlite", "database", "redis")


def _url_do_banco_e_compartilhada() -> bool:
    from app.core.config import get_settings  # noqa: PLC0415

    try:
        url = get_settings().sqlalchemy_database_url
    except Exception:  # pragma: no cover - configuração ausente
        return False
    return not url.startswith("sqlite")


def build_backend() -> CacheBackend:
    escolha = (os.environ.get("CACHE_BACKEND") or "").strip().lower()
    url = (os.environ.get("REDIS_URL") or "").strip()

    if escolha and escolha not in BACKENDS_CONHECIDOS:
        raise RuntimeError(
            f"CACHE_BACKEND={escolha!r} não existe. "
            f"Os backends são: {', '.join(BACKENDS_CONHECIDOS)}. "
            "Errar o nome em silêncio devolveria cache por nó sem ninguém notar."
        )

    if escolha == "sqlite":
        return SqliteBackend()

    if escolha == "database":
        logger.info("Cache no banco da aplicação.")
        return DatabaseBackend()

    if escolha == "redis" or url:
        if not url:
            raise RuntimeError("CACHE_BACKEND=redis exige REDIS_URL.")
        logger.info("Cache compartilhado via Redis.")
        return RedisBackend(url)

    if _url_do_banco_e_compartilhada():
        logger.info("Cache no banco da aplicação (padrão com banco compartilhado).")
        return DatabaseBackend()

    return SqliteBackend()
