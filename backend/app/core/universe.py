from __future__ import annotations

import logging
import re
import threading
import time

from app.core import cache

logger = logging.getLogger(__name__)

_UNIVERSE_CACHE_KEY = "mercado_universe_v1"
_LISTA_CACHE_KEY = "mercado_lista_v1"
_UNIVERSE_TTL = 12 * 3600

_FRACTIONAL_LOT = re.compile(r"^[A-Z]{4}\d{1,2}F$")


def _ler_lista() -> list[dict]:
    from app.collectors import mercado

    try:
        return mercado.ler_lista()
    except Exception as e:
        logger.warning("Falha ao ler a lista de ativos da base de mercado: %s", e)
        return []


def _lista() -> list[dict]:
    cached = cache.get(_LISTA_CACHE_KEY)
    if cached is not None:
        return cached

    lista = _ler_lista()
    if lista:
        cache.set(_LISTA_CACHE_KEY, lista, _UNIVERSE_TTL)
        return lista

    vencida, _ = cache.get_with_age(_LISTA_CACHE_KEY)
    return vencida or []


_MEMO_TTL = 15 * 60
_memo_lock = threading.Lock()
_memo: dict[str, tuple[float, object]] = {}


def _memoized(key: str, build):
    now = time.monotonic()
    cached = _memo.get(key)
    if cached is not None and (now - cached[0]) < _MEMO_TTL:
        return cached[1]

    with _memo_lock:
        cached = _memo.get(key)
        if cached is not None and (time.monotonic() - cached[0]) < _MEMO_TTL:
            return cached[1]
        value = build()
        _memo[key] = (time.monotonic(), value)
        return value


def invalidate_universe_memo() -> None:
    with _memo_lock:
        _memo.clear()


def get_sector_map() -> dict[str, str]:
    return _memoized(
        "sector_map", lambda: {a["codigo"]: a["setor"] for a in _lista() if a.get("setor")}
    )


def get_type_map() -> dict[str, str]:
    return _memoized(
        "type_map", lambda: {a["codigo"]: a["tipo"] for a in _lista() if a.get("tipo")}
    )


def _get_search_index() -> list[tuple[str, str, str]]:
    def _build() -> list[tuple[str, str, str]]:
        index = []
        for a in _lista():
            if _FRACTIONAL_LOT.match(a["codigo"]):
                continue
            nome = a.get("nome") or ""
            index.append((a["codigo"].upper(), nome, nome.upper()))
        return index

    return _memoized("search_index", _build)


_QUANTOS = {"stock": 150, "fii": 60, "bdr": 40, "etf": 30}


def _montar_universo() -> list[str]:
    lista = _lista()
    if not lista:
        return []

    tickers = []
    for tipo, quantos in _QUANTOS.items():
        da_classe = [
            a
            for a in lista
            if a.get("tipo") == tipo
            and (a.get("volume_medio") or 0) > 0
            and not _FRACTIONAL_LOT.match(a["codigo"])
        ]
        da_classe.sort(key=lambda a: a["volume_medio"], reverse=True)
        tickers += [a["codigo"] for a in da_classe[:quantos]]
    return tickers


def get_universe() -> list[str]:
    cached = cache.get(_UNIVERSE_CACHE_KEY)
    if cached is not None:
        return cached

    tickers = _montar_universo()
    if tickers:
        cache.set(_UNIVERSE_CACHE_KEY, tickers, _UNIVERSE_TTL)
        return tickers

    vencido, idade = cache.get_with_age(_UNIVERSE_CACHE_KEY)
    if vencido:
        logger.warning(
            "A base de mercado não deu a lista — servindo o universo vencido há %.0f s.",
            idade or 0.0,
        )
        return vencido

    logger.warning("A base de mercado não deu a lista e não há universo em cache — universo vazio.")
    return []


def search_universe(query: str, limit: int = 10) -> list[dict]:
    q = query.strip().upper()
    if not q:
        return []

    results = [
        {"ticker": ticker, "name": name}
        for ticker, name, name_upper in _get_search_index()
        if q in ticker or q in name_upper
    ]

    results.sort(key=lambda r: (not r["ticker"].startswith(q), r["ticker"]))
    return results[:limit]
