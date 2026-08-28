from __future__ import annotations

import asyncio
import contextlib
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
        # O lock do job periódico NÃO é liberado no fim do ciclo de propósito: o
        # TTL é o próprio intervalo. Liberar deixaria o worker seguinte rodar o
        # mesmo ciclo segundos depois — que é exatamente o que o lock evita.

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
    from app.core import sessions, usage
    from app.storage import event_store

    removed = await asyncio.to_thread(cache.purge_expired)
    if removed:
        logger.info("Manutenção de cache: %d entradas vencidas removidas.", removed)

    for label, purge in (
        ("denylist de sessão", sessions.purge_expired),
        ("contadores de uso", usage.purge_expired),
        ("eventos de produto", event_store.purge_old),
    ):
        count = await asyncio.to_thread(purge)
        if count:
            logger.info("Manutenção: %d linha(s) removida(s) de %s.", count, label)


WARM_UP_LOCK = "market_scan_warmup"
WARM_UP_LOCK_TTL = 10 * 60


async def warm_up_market_scan() -> None:
    """Aquece o cache de oportunidades — uma vez por frota, não uma por worker.

    Sem lock, subir três réplicas disparava três varreduras do universo inteiro
    ao mesmo tempo, que é o pico de consumo de cota mais caro que o produto tem.
    """
    from app.services import OpportunityService

    acquired = await asyncio.to_thread(
        portfolio_store.try_acquire_job_lock, WARM_UP_LOCK, WORKER_ID, WARM_UP_LOCK_TTL
    )
    if not acquired:
        logger.info("Warm-up de oportunidades já em curso em outro worker; pulando.")
        return

    try:
        await OpportunityService()._scan_market()
        logger.info("Cache de oportunidades aquecido no startup.")
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.warning("Falha ao aquecer cache de oportunidades no startup", exc_info=True)
    finally:
        with contextlib.suppress(Exception):
            await asyncio.to_thread(portfolio_store.release_job_lock, WARM_UP_LOCK, WORKER_ID)


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
