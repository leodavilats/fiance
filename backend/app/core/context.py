from __future__ import annotations

import contextvars

from app.core.errors import DomainError

_current_user_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_user_id", default=None
)


class MissingUserContextError(DomainError):
    """Operação de tenant sem usuário no contexto."""

    status_code = 401


def get_current_user_id() -> str:
    user_id = _current_user_id.get()
    if not user_id:
        raise MissingUserContextError(
            "Nenhum usuário no contexto da requisição — operação de tenant abortada."
        )
    return user_id


def get_current_user_id_or_none() -> str | None:
    """Para jobs de background, que legitimamente rodam fora de uma requisição."""
    return _current_user_id.get()


def set_current_user_id(user_id: str) -> contextvars.Token:
    return _current_user_id.set(user_id)


def reset_current_user_id(token: contextvars.Token) -> None:
    _current_user_id.reset(token)


_request_session: contextvars.ContextVar[object | None] = contextvars.ContextVar(
    "request_session", default=None
)


def get_request_session():
    return _request_session.get()


def set_request_session(session) -> contextvars.Token:
    return _request_session.set(session)


def reset_request_session(token: contextvars.Token) -> None:
    _request_session.reset(token)


_request_memo: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "request_memo", default=None
)


def set_request_memo() -> contextvars.Token:
    return _request_memo.set({})


def reset_request_memo(token: contextvars.Token) -> None:
    _request_memo.reset(token)


async def memoize_request(key: str, factory):
    """Executa `factory()` uma vez por request, memoizando por `key`."""
    memo = _request_memo.get()
    if memo is None:
        return await factory()

    if key not in memo:
        memo[key] = await factory()
    return memo[key]
