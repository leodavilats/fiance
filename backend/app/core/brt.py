from __future__ import annotations

from datetime import datetime, timedelta, timezone

"""Fuso de referência fiscal: horário de Brasília."""

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
