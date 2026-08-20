from __future__ import annotations

from datetime import datetime, timedelta, timezone

"""Fuso de referência fiscal: horário de Brasília.

A isenção mensal de R$ 20 mil e as faixas de IR são apuradas por **mês
calendário brasileiro**. O cálculo era feito em fronteira de mês UTC: uma venda
no último dia do mês depois das 21 h BRT caía no mês seguinte, mudando o balde
da isenção e a alíquota.

O Brasil não usa horário de verão desde 2019, então um offset fixo de UTC-3 é
exato e evita depender do pacote `tzdata` (ausente por padrão no Windows).
"""

BRT = timezone(timedelta(hours=-3), name="BRT")


def now_brt() -> datetime:
    return datetime.now(BRT)


def to_brt(timestamp: float) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=BRT)


def month_start_timestamp(timestamp: float | None = None) -> float:
    """Início do mês calendário brasileiro que contém `timestamp`."""
    moment = to_brt(timestamp) if timestamp is not None else now_brt()
    start = moment.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start.timestamp()


def month_key(timestamp: float) -> str:
    """Chave YYYY-MM no fuso brasileiro."""
    return to_brt(timestamp).strftime("%Y-%m")
