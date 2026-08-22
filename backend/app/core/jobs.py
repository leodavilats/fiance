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

WORKER_ID = f"{socket.gethostname()}:{os.getpid()}"


async def _run_guarded(
    name: str,
    interval_seconds: float,
    lock_ttl_seconds: float,
    body: Callable[[], Awaitable[None]],
    initial_delay_seconds: float = 0.0,
) -> None:
    """Roda `body` em intervalos, com lock cooperativo entre workers."""
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
                lock_ttl_seconds=NOTIFICATION_INTERVAL * 0.9,
                body=_notification_body,
                initial_delay_seconds=60,
            ),
            name="notification-loop",
        ),
        asyncio.create_task(
            _run_guarded(
                "daily_snapshot",
                interval_seconds=SNAPSHOT_INTERVAL,
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
