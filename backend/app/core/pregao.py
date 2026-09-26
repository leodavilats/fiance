from __future__ import annotations

from datetime import date, datetime, time, timedelta
from functools import lru_cache

from app.core.brt import BRT, now_brt

ABERTURA = time(10, 0)

ABERTURA_CINZAS = time(13, 0)

FECHAMENTO = time(18, 30)

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


def quarta_de_cinzas(ano: int) -> date:
    return pascoa(ano) - timedelta(days=46)


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


def abertura(dia: date) -> time:
    return ABERTURA_CINZAS if dia == quarta_de_cinzas(dia.year) else ABERTURA


def em_pregao(momento: datetime | None = None) -> bool:
    agora = momento or now_brt()
    if agora.tzinfo is not None:
        agora = agora.astimezone(BRT)
    dia = agora.date()

    if not ha_pregao(dia):
        return False

    return abertura(dia) <= agora.time() <= FECHAMENTO
