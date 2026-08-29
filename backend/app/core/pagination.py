from __future__ import annotations

import base64
import binascii
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from app.core.errors import DomainError

MAX_PAGE_SIZE = 500

DEFAULT_PAGE_SIZE = 200


class InvalidCursorError(DomainError):
    status_code = 400


def encode_cursor(sort_value: Any, row_id: Any) -> str:
    payload = json.dumps({"k": sort_value, "i": row_id}, ensure_ascii=False, default=str)
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> tuple[Any, Any]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
        return payload["k"], payload["i"]
    except (binascii.Error, UnicodeDecodeError, ValueError, KeyError, TypeError) as exc:
        raise InvalidCursorError(
            "Cursor de paginação inválido. Recomece a listagem sem o parâmetro `cursor`."
        ) from exc


def clamp_limit(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_PAGE_SIZE
    return max(1, min(int(limit), MAX_PAGE_SIZE))


T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    items: list[T]
    next_cursor: str | None
    has_more: bool

    def as_dict(self) -> dict:
        return {"next_cursor": self.next_cursor, "has_more": self.has_more}


def paginate(
    rows: list[T],
    limit: int,
    key: Callable[[T], Any],
    identity: Callable[[T], Any],
) -> Page[T]:
    has_more = len(rows) > limit
    page = rows[:limit]

    next_cursor = None
    if has_more and page:
        last = page[-1]
        next_cursor = encode_cursor(key(last), identity(last))

    return Page(items=page, next_cursor=next_cursor, has_more=has_more)


def apply_keyset(stmt, sort_column, id_column, cursor: str | None, descending: bool = True):
    if descending:
        stmt = stmt.order_by(sort_column.desc(), id_column.desc())
    else:
        stmt = stmt.order_by(sort_column.asc(), id_column.asc())

    if cursor is None:
        return stmt

    sort_value, row_id = decode_cursor(cursor)

    if descending:
        return stmt.where(
            (sort_column < sort_value) | ((sort_column == sort_value) & (id_column < row_id))
        )
    return stmt.where(
        (sort_column > sort_value) | ((sort_column == sort_value) & (id_column > row_id))
    )


def slice_after(
    rows: list[T],
    cursor: str | None,
    limit: int,
    key: Callable[[T], Any],
    identity: Callable[[T], Any],
    descending: bool = True,
) -> Page[T]:
    if cursor is not None:
        anchor = decode_cursor(cursor)
        if descending:
            rows = [row for row in rows if (key(row), identity(row)) < anchor]
        else:
            rows = [row for row in rows if (key(row), identity(row)) > anchor]

    return paginate(rows, limit, key, identity)
