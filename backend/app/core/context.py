from __future__ import annotations

import contextvars

_current_user_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_user_id", default="default"
)


def get_current_user_id() -> str:
    return _current_user_id.get()


def set_current_user_id(user_id: str) -> contextvars.Token:
    return _current_user_id.set(user_id)


def reset_current_user_id(token: contextvars.Token) -> None:
    _current_user_id.reset(token)
