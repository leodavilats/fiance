from __future__ import annotations

import asyncio
import logging
import os
import socket
import time
from collections.abc import Awaitable, Callable

from app.core import cache
from app.storage import portfolio_store

logger = logging.getLogger("fiance.jobs")

# Identidade deste processo, para o lock saber quem é o dono atual.
WORKER_ID = f"{socket.gethostname()}:{os.getpid()}"


async def _run_guarded(
    name: str,
    interval_seconds: float,
    lock_ttl_seconds: float,
    body: Callable[[], Awaitable[None]],
    initial_delay_seconds: float = 0.0,
) -> None:
    """Roda `body` em intervalos, com lock cooperativo entre workers.

    Sem o lock, cada worker/dyno rodava o próprio ciclo: o de notificação
    gerava push duplicado para o mesmo usuário. O lock expira sozinho, então um
    worker que morra no meio não trava o job para sempre.
    """
    if initial_delay_seconds:
        await asyncio.sleep(initial_delay_seconds)

    while True:
        started = time.monotonic()
        try:
            acquired = await asyncio.to_thread(
                portfolio_store.try_acquire_job_lock, name, WORKER_ID, lock_ttl_seconds
            )
            if acquired:
                await body()
            else:
                logger.debug("Job %s já está rodando em outro worker; pulando ciclo.", name)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.warning("Falha no job %s", name, exc_info=True)

        if not interval_seconds:
            return

        elapsed = time.monotonic() - started
        await asyncio.sleep(max(interval_seconds - elapsed, 1.0))


async def _notification_body() -> None:
    from app.services.notification_job import run_notification_cycle

    await run_notification_cycle()


async def _snapshot_body() -> None:
    from app.services.snapshot_job import run_snapshot_cycle

    await run_snapshot_cycle()


async def _maintenance_body() -> None:
    removed = await asyncio.to_thread(cache.purge_expired)
    if removed:
        logger.info("Manutenção de cache: %d entradas vencidas removidas.", removed)


async def warm_up_market_scan() -> None:
    from app.services import OpportunityService

    try:
        # Aquece só o dado de mercado (independe de preferência do usuário) —
        # a personalização é calculada por request.
        await OpportunityService()._scan_market()
        logger.info("Cache de oportunidades aquecido no startup.")
    except Exception:
        logger.warning("Falha ao aquecer cache de oportunidades no startup", exc_info=True)


NOTIFICATION_INTERVAL = 15 * 60
SNAPSHOT_INTERVAL = 6 * 3600
MAINTENANCE_INTERVAL = 6 * 3600


def start_background_jobs() -> list[asyncio.Task]:
    return [
        asyncio.create_task(warm_up_market_scan(), name="warm-up-market-scan"),
        asyncio.create_task(
            _run_guarded(
                "notifications",
                interval_seconds=NOTIFICATION_INTERVAL,
                # TTL menor que o intervalo: se este worker morrer, outro assume
                # no próximo ciclo em vez de esperar o TTL inteiro.
                lock_ttl_seconds=NOTIFICATION_INTERVAL * 0.9,
                body=_notification_body,
                # Espera o warm-up preencher o cache pra não pagar o scan 2x.
                initial_delay_seconds=60,
            ),
            name="notification-loop",
        ),
        asyncio.create_task(
            _run_guarded(
                "daily_snapshot",
                interval_seconds=SNAPSHOT_INTERVAL,
                # O snapshot sobrescreve o registro do dia (day_key), então
                # rodar mais de uma vez por dia é idempotente por construção —
                # o intervalo curto só garante que o dia não passe em branco se
                # o processo reiniciar.
                lock_ttl_seconds=SNAPSHOT_INTERVAL * 0.9,
                body=_snapshot_body,
                initial_delay_seconds=120,
            ),
            name="snapshot-loop",
        ),
        asyncio.create_task(
            _run_guarded(
                "cache_maintenance",
                interval_seconds=MAINTENANCE_INTERVAL,
                lock_ttl_seconds=MAINTENANCE_INTERVAL * 0.9,
                body=_maintenance_body,
                initial_delay_seconds=300,
            ),
            name="maintenance-loop",
        ),
    ]
