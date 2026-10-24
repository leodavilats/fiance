from __future__ import annotations

from datetime import date, datetime, time, timedelta
from functools import lru_cache

from app.core.brt import BRT, now_brt

CARGA = time(23, 0)

_FIXOS = (
    (1, 1),
    (4, 21),
    (5, 1),
    (9, 7),
    (10, 12),
    (11, 2),
    (11, 15),
    (12, 24),
    (12, 25),
    (12, 31),
)

_CONSCIENCIA_NEGRA_NACIONAL_DESDE = 2024


def pascoa(ano: int) -> date:
    a = ano % 19
    b, c = divmod(ano, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    el = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * el) // 451
    mes, dia = divmod(h + el - 7 * m + 114, 31)
    return date(ano, mes, dia + 1)


@lru_cache(maxsize=32)
def dias_sem_pregao(ano: int) -> frozenset[date]:
    domingo = pascoa(ano)
    dias = {date(ano, mes, dia) for mes, dia in _FIXOS}
    if ano >= _CONSCIENCIA_NEGRA_NACIONAL_DESDE:
        dias.add(date(ano, 11, 20))
    dias.update(
        {
            domingo - timedelta(days=48),
            domingo - timedelta(days=47),
            domingo - timedelta(days=2),
            domingo + timedelta(days=60),
        }
    )
    return frozenset(dias)


def ha_pregao(dia: date) -> bool:
    return dia.weekday() < 5 and dia not in dias_sem_pregao(dia.year)


def deslocar_pregoes(dia: date, pregoes: int) -> date:
    passo = timedelta(days=1 if pregoes > 0 else -1)
    restantes = abs(pregoes)
    while restantes:
        dia += passo
        if ha_pregao(dia):
            restantes -= 1
    return dia


def _em_brasilia(momento: datetime | None) -> datetime:
    agora = momento or now_brt()
    return agora.astimezone(BRT) if agora.tzinfo is not None else agora.replace(tzinfo=BRT)


def ultimo_pregao_carregado(momento: datetime | None = None) -> date:
    agora = _em_brasilia(momento)
    dia = agora.date()
    if ha_pregao(dia) and agora.time() >= CARGA:
        return dia
    return deslocar_pregoes(dia, -1)


def proxima_carga(momento: datetime | None = None) -> datetime:
    agora = _em_brasilia(momento)
    dia = agora.date()
    if not (ha_pregao(dia) and agora.time() < CARGA):
        dia = deslocar_pregoes(dia, 1)
    return datetime.combine(dia, CARGA, tzinfo=BRT)
