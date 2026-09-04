from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.core.cache_backends import DB_PATH, CacheBackend, SqliteBackend, build_backend

logger = logging.getLogger("fiance.cache")

__all__ = [
    "DB_PATH",
    "backend",
    "clear_all",
    "delete",
    "delete_pattern",
    "get",
    "get_with_age",
    "purge_expired",
    "reset_connection",
    "set",
    "set_backend",
]

_backend: CacheBackend | None = None


def backend() -> CacheBackend:
    global _backend
    if _backend is None:
        _backend = build_backend()
    return _backend


def set_backend(novo: CacheBackend | None) -> None:
    global _backend
    _backend = novo


def _record_lookup(hit: bool) -> None:
    try:
        from app.core.observability import record_cache_lookup

        record_cache_lookup(hit)
    except Exception:
        pass


def reset_connection() -> None:
    atual = _backend
    if atual is not None and hasattr(atual, "reset_connection"):
        atual.reset_connection()
    set_backend(None)


def get(key: str) -> Any | None:
    row = backend().get_raw(key)

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
    row = backend().get_raw(key)
    if not row:
        return None, None

    value, expires_at = row
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None, None

    return parsed, max(0.0, time.time() - expires_at)


def set(key: str, value: Any, ttl_seconds: int) -> None:
    backend().set_raw(key, json.dumps(value, default=str), time.time() + ttl_seconds)


def delete(key: str) -> None:
    backend().delete(key)


def delete_pattern(pattern: str) -> int:
    return backend().delete_pattern(pattern)


def clear_all() -> int:
    return backend().clear_all()


def purge_expired() -> int:
    return backend().purge_expired()


def describe() -> dict:
    atual = backend()
    compartilhado = bool(getattr(atual, "shared", atual.name != "sqlite"))
    return {
        "backend": atual.name,
        "shared": compartilhado,
        "note": (
            "Cache compartilhado entre os nós."
            if compartilhado
            else "Cache por nó. Com mais de um nó, a mesma pessoa pode ver preços "
            "diferentes conforme o balanceador — use CACHE_BACKEND=database ou REDIS_URL."
        ),
    }


def _sqlite_backend_for_tests() -> SqliteBackend:
    novo = SqliteBackend()
    set_backend(novo)
    return novo
