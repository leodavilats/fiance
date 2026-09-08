"""O que a carteira da pessoa rende ao mês, e o CDI como segunda opção.

Vive fora de `api/` porque dois consumidores precisam da mesma resposta: a régua de dívida, que
compara o custo de uma dívida com o que a carteira rende, e o aporte, que precisa da cascata para
saber quanto sobrou depois da dívida e da reserva.
"""

from __future__ import annotations

import logging

from app.collectors import rates
from app.services.benchmark_service import BenchmarkService
from app.storage import portfolio_store

logger = logging.getLogger("fiance.cashflow")


async def referencia_de_rendimento() -> tuple[float | None, bool, float | None]:
    tem_carteira = portfolio_store.has_holdings()

    cdi_anual: float | None = None
    try:
        cdi_anual = rates.get_rates().get("cdi_anual")
    except Exception as exc:
        logger.warning("CDI indisponível para a régua de dívida: %s", exc)

    if not tem_carteira:
        return None, False, cdi_anual

    try:
        benchmark = await BenchmarkService().get_benchmark()
        total_pct = benchmark.portfolio_return_pct
    except Exception as exc:
        logger.warning("Retorno da carteira indisponível: %s", exc)
        return None, False, cdi_anual

    if not benchmark.points:
        return None, False, cdi_anual

    # O retorno vem acumulado na série, e a série é diária: mensalizar por composto sobre o
    # número de meses, não sobre o número de pontos.
    meses = max(1.0, len(benchmark.points) / 21.0)
    mensal = ((1.0 + total_pct / 100.0) ** (1.0 / meses) - 1.0) * 100.0
    return mensal, True, cdi_anual
