from __future__ import annotations

import math

from fastapi import Depends, HTTPException, Request

from app.core import usage
from app.core.auth import get_current_user
from app.core.config import get_settings

DEFAULT_PER_MINUTE = 240

EXPENSIVE_PER_MINUTE = 12
EXPENSIVE_SUFFIXES = (
    "/opportunities",
    "/dip-scanner",
    "/strategy",
    "/quick-invest",
    "/dashboard",
    "/sectors-summary",
)

WRITE_PER_MINUTE = 60


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "path", None) or request.url.path


def _is_expensive(path: str) -> bool:
    return any(path == suffix or path.endswith(suffix) for suffix in EXPENSIVE_SUFFIXES)


def _limit_for(request: Request, path: str) -> int:
    if _is_expensive(path):
        return EXPENSIVE_PER_MINUTE
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        return WRITE_PER_MINUTE
    return DEFAULT_PER_MINUTE


async def rate_limit(request: Request, user_id: str = Depends(get_current_user)) -> None:
    settings = get_settings()
    if not settings.rate_limit_enabled:
        return

    path = _route_template(request)
    limit = math.ceil(_limit_for(request, path) * settings.rate_limit_factor)
    if limit <= 0:
        return

    resource = f"route:{request.method} {path}"
    window = usage.minute_window()
    count = usage.increment(user_id, resource, window, ttl_seconds=usage.MINUTE * 2)

    if count > limit:
        raise HTTPException(
            status_code=429,
            detail=(
                "Muitas requisições para esta rota em pouco tempo. "
                "Aguarde um minuto e tente de novo."
            ),
            headers={"Retry-After": "60"},
        )


def client_ip(request: Request) -> str:
    peer = request.client.host if request.client else "desconhecido"

    confiaveis = get_settings().trusted_proxy_count
    if confiaveis <= 0:
        return peer

    cadeia = [p.strip() for p in request.headers.get("X-Forwarded-For", "").split(",") if p.strip()]
    if len(cadeia) < confiaveis:
        return peer

    return cadeia[-confiaveis]


async def ip_rate_limit(
    request: Request,
    resource: str,
    per_minute: int,
    cost: int = 1,
) -> None:
    settings = get_settings()
    if not settings.rate_limit_enabled:
        return

    limite = math.ceil(per_minute * settings.rate_limit_factor)
    if limite <= 0:
        return

    count = usage.increment(
        f"ip:{client_ip(request)}",
        resource,
        usage.minute_window(),
        ttl_seconds=usage.MINUTE * 2,
        amount=cost,
    )
    if count > limite:
        raise HTTPException(
            status_code=429,
            detail="Muitas requisições. Aguarde um minuto e tente de novo.",
            headers={"Retry-After": "60"},
        )
