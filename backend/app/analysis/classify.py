from __future__ import annotations

from typing import Optional

def auto_category(

    asset_type: str,

    dividend_yield: Optional[float],

    has_dividend_history: bool = False,

) -> str:

    if asset_type == "fii":

        return "renda"

    if asset_type == "crypto":

        return "trade"

    dy = dividend_yield or 0.0

    if dy >= 4.0 and has_dividend_history:

        return "renda"

    return "trade"

def resolve_category(stored: str, auto: str) -> str:

    if stored in ("renda", "trade"):

        return stored

    return auto

