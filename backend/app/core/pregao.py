from __future__ import annotations

from datetime import datetime, time

from app.core.brt import now_brt

ABERTURA = time(10, 0)

FECHAMENTO = time(18, 30)


def em_pregao(momento: datetime | None = None) -> bool:
    agora = momento or now_brt()

    if agora.weekday() >= 5:
        return False

    return ABERTURA <= agora.time() <= FECHAMENTO
