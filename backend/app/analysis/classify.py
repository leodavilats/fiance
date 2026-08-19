from __future__ import annotations

_LEGACY_MAP = {
    "renda": "fiis",
    "trade": "acoes_br",
    "caixa": "renda_fixa",
}

VALID_CATEGORIES = {"renda_fixa", "acoes_br", "bdrs", "fiis", "etfs"}


def auto_category(
    asset_type: str,
    dividend_yield: float | None = None,
    has_dividend_history: bool = False,
) -> str:
    if asset_type == "fii":
        return "fiis"
    if asset_type == "etf":
        return "etfs"
    if asset_type == "bdr":
        return "bdrs"
    return "acoes_br"


def resolve_category(stored: str, auto: str) -> str:
    if stored in VALID_CATEGORIES:
        return stored

    if stored in _LEGACY_MAP:
        return _LEGACY_MAP[stored]
    return auto
