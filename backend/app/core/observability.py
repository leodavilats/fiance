from __future__ import annotations

import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field

from app.core.context import (
    get_request_session,
    reset_request_memo,
    reset_request_session,
    set_request_memo,
    set_request_session,
)
from app.core.database import SessionLocal

"""Instrumentação mínima.

Não havia métrica, tracing nem ID de correlação: era impossível saber quantas
chamadas à BRAPI foram feitas, qual a taxa de cache hit ou qual endpoint está
lento em produção — e é exatamente essa informação que decide as prioridades de
performance. Contadores em processo, expostos em `GET /metrics`.
"""


@dataclass
class _Latency:
    count: int = 0
    total_ms: float = 0.0
    max_ms: float = 0.0

    def observe(self, elapsed_ms: float) -> None:
        self.count += 1
        self.total_ms += elapsed_ms
        self.max_ms = max(self.max_ms, elapsed_ms)

    def as_dict(self) -> dict:
        return {
            "count": self.count,
            "avg_ms": round(self.total_ms / self.count, 1) if self.count else 0.0,
            "max_ms": round(self.max_ms, 1),
        }


@dataclass
class _Metrics:
    started_at: float = field(default_factory=time.time)
    counters: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    latency_by_route: dict[str, _Latency] = field(default_factory=dict)

    lock: threading.Lock = field(default_factory=threading.Lock)

    def incr(self, name: str, amount: int = 1) -> None:
        with self.lock:
            self.counters[name] += amount

    def observe_route(self, route: str, elapsed_ms: float) -> None:
        with self.lock:
            self.latency_by_route.setdefault(route, _Latency()).observe(elapsed_ms)

    def snapshot(self) -> dict:
        with self.lock:
            counters = dict(self.counters)
            routes = {
                route: latency.as_dict()
                for route, latency in sorted(
                    self.latency_by_route.items(),
                    key=lambda kv: -kv[1].total_ms,
                )
            }

        cache_hits = counters.get("cache.hit", 0)
        cache_misses = counters.get("cache.miss", 0)
        total_lookups = cache_hits + cache_misses

        return {
            "uptime_seconds": round(time.time() - self.started_at, 1),
            "counters": counters,
            "cache_hit_rate": round(cache_hits / total_lookups, 4) if total_lookups else None,
            "latency_by_route": routes,
        }

    def reset(self) -> None:
        with self.lock:
            self.counters.clear()
            self.latency_by_route.clear()
            self.started_at = time.time()


metrics = _Metrics()


def record_external_call(provider: str, ok: bool) -> None:
    metrics.incr(f"external.{provider}.{'ok' if ok else 'error'}")


def record_cache_lookup(hit: bool) -> None:
    metrics.incr("cache.hit" if hit else "cache.miss")


# --- middleware -----------------------------------------------------------


def _route_label(request) -> str:
    """Rota sem os parâmetros de path, para não explodir a cardinalidade."""
    route = request.scope.get("route")
    template = getattr(route, "path", None)
    return f"{request.method} {template or request.url.path}"


async def observability_middleware(request, call_next):
    """ID de correlação, latência por rota e sessão de banco por request."""
    correlation_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:16]
    request.state.correlation_id = correlation_id

    started = time.perf_counter()

    session = SessionLocal()
    token = set_request_session(session)
    memo_token = set_request_memo()
    try:
        response = await call_next(request)
        # Só commita quando a resposta saiu sem exceção: um handler que falhou
        # no meio não deve deixar escrita parcial no banco.
        if get_request_session() is session:
            session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        reset_request_memo(memo_token)
        reset_request_session(token)
        session.close()
        elapsed_ms = (time.perf_counter() - started) * 1000
        metrics.observe_route(_route_label(request), elapsed_ms)

    response.headers["X-Request-Id"] = correlation_id
    return response
