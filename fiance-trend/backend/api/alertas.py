from __future__ import annotations

from datetime import date, datetime, timedelta

import numpy as np

RODADA_ATRASADA = timedelta(hours=80)
RODADA_TRAVADA = timedelta(hours=6)
DIAS_UTEIS_SEM_COTACAO = 2


def avaliar(
    rodada: dict | None, ultima_cotacao: date | None, agora: datetime, hoje: date
) -> list[dict]:
    alertas = []
    if rodada is None:
        alertas.append({"tipo": "rodada", "mensagem": "O data-job nunca registrou uma rodada."})
    else:
        if agora - rodada["iniciada_em"] > RODADA_ATRASADA:
            alertas.append(
                {
                    "tipo": "rodada",
                    "mensagem": "Nenhuma rodada do data-job desde "
                    f"{rodada['iniciada_em']:%d/%m/%Y %H:%M} (UTC).",
                }
            )
        if rodada["terminada_em"] is None and agora - rodada["iniciada_em"] > RODADA_TRAVADA:
            alertas.append(
                {"tipo": "rodada", "mensagem": "A última rodada começou e não terminou."}
            )
        for etapa, erro in (rodada["falhas"] or {}).items():
            alertas.append(
                {"tipo": "etapa", "mensagem": f"{etapa} falhou na última rodada: {erro}"}
            )
    if ultima_cotacao is not None:
        atraso = int(np.busday_count(ultima_cotacao + timedelta(days=1), hoje))
        if atraso > DIAS_UTEIS_SEM_COTACAO:
            alertas.append(
                {
                    "tipo": "cotacao",
                    "mensagem": f"A última cotação é de {ultima_cotacao:%d/%m/%Y}: "
                    f"{atraso} dias úteis sem pregão novo.",
                }
            )
    return alertas
