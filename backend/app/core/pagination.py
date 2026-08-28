"""Paginação por cursor (keyset), e não por offset.

`OFFSET n` relê e descarta as n primeiras linhas a cada página — fica mais lento
conforme o usuário avança — e, pior, **pula ou repete** itens quando algo é
inserido entre duas páginas. Numa lista ordenada por data decrescente, registrar
um provento novo enquanto se folheia empurra tudo para baixo e o item da borda
aparece duas vezes. Num extrato que vira declaração, isso não é aceitável.

O cursor aqui é a última chave lida: `(valor_de_ordenação, id)`. A página
seguinte pede "o que vem depois desta chave", então inserção não desloca nada.
O `id` está lá como desempate — sem ele, dois registros do mesmo dia fariam a
paginação travar ou pular.

O cursor é opaco de propósito: base64 de um JSON interno. Não é segredo — é para
que a forma da chave possa mudar sem quebrar cliente que a tenha guardado.
"""

from __future__ import annotations

import base64
import binascii
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from app.core.errors import DomainError

#: Teto de segurança. Existe para que uma lista sem paginação no cliente não
#: cresça sem limite com o uso — o `has_more` diz a verdade sobre o resto.
MAX_PAGE_SIZE = 500

#: Tamanho padrão quando o cliente não pede nada. Generoso porque a maioria das
#: carteiras cabe numa página só, e apertar isso truncaria telas que hoje
#: funcionam sem que ninguém percebesse.
DEFAULT_PAGE_SIZE = 200


class InvalidCursorError(DomainError):
    """Cursor corrompido ou de outra listagem."""

    status_code = 400


def encode_cursor(sort_value: Any, row_id: Any) -> str:
    payload = json.dumps({"k": sort_value, "i": row_id}, ensure_ascii=False, default=str)
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> tuple[Any, Any]:
    """Devolve `(valor_de_ordenação, id)`. Cursor inválido é 400, não 500."""
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
    """Uma fatia da lista, com o endereço da próxima."""

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
    """Corta a lista no limite e monta o cursor a partir do último item.

    Recebe **uma linha a mais** que o limite quando quem chama souber pedir
    assim — é como se descobre que há próxima página sem um `COUNT(*)` extra
    sobre a tabela inteira.
    """
    has_more = len(rows) > limit
    page = rows[:limit]

    next_cursor = None
    if has_more and page:
        last = page[-1]
        next_cursor = encode_cursor(key(last), identity(last))

    return Page(items=page, next_cursor=next_cursor, has_more=has_more)


def apply_keyset(stmt, sort_column, id_column, cursor: str | None, descending: bool = True):
    """Adiciona ordenação estável e o corte do cursor a um `select`.

    A comparação é lexicográfica sobre a tupla `(ordenação, id)`, escrita à mão
    porque nem todo banco suportado aceita comparação de tupla — e porque a
    versão expandida deixa visível que o `id` só desempata.
    """
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
    """Pagina em memória uma lista já ordenada.

    Existe para as listas cujo agregado precisa do conjunto inteiro por
    definição — total por mês, marcação a mercado, comparação contra o Ibovespa.
    Nesses casos a **consulta** continua completa e o que fica limitado é o
    payload: cortar no banco faria o total falar só da página, e total errado é
    pior que lista longa.

    Onde não há agregado, use `apply_keyset` e corte no banco de verdade.
    """
    if cursor is not None:
        anchor = decode_cursor(cursor)
        if descending:
            rows = [row for row in rows if (key(row), identity(row)) < anchor]
        else:
            rows = [row for row in rows if (key(row), identity(row)) > anchor]

    return paginate(rows, limit, key, identity)
