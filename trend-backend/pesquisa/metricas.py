from __future__ import annotations

import numpy as np
import pandas as pd

from pesquisa.motor import Resultado

PREGOES_POR_ANO = 252


def _anual(serie: pd.Series) -> float:
    anos = (len(serie) - 1) / PREGOES_POR_ANO
    return float((serie.iloc[-1] / serie.iloc[0]) ** (1 / anos) - 1) if anos > 0 else 0.0


def resumir(resultado: Resultado) -> dict:
    carteira, cdi = resultado.patrimonio, resultado.cdi
    diario = carteira.pct_change().dropna()
    excesso = diario - cdi.pct_change().dropna()
    queda = carteira / carteira.cummax() - 1
    mensal = carteira.resample("ME").last().pct_change().dropna()
    cdi_mensal = cdi.resample("ME").last().pct_change().dropna()
    desvio = excesso.std()
    return {
        "inicio": str(carteira.index[0].date()),
        "fim": str(carteira.index[-1].date()),
        "retorno_anual": round(_anual(carteira), 4),
        "cdi_anual": round(_anual(cdi), 4),
        "excesso_anual": round(_anual(carteira) - _anual(cdi), 4),
        "volatilidade_anual": round(float(diario.std() * np.sqrt(PREGOES_POR_ANO)), 4),
        "sharpe_sobre_cdi": round(float(excesso.mean() / desvio * np.sqrt(PREGOES_POR_ANO)), 3)
        if desvio > 0
        else 0.0,
        "pior_queda": round(float(queda.min()), 4),
        "meses_acima_do_cdi": round(float((mensal > cdi_mensal.reindex(mensal.index)).mean()), 3),
        "giro_mensal_medio": round(float(np.mean(resultado.giro)), 3) if resultado.giro else 0.0,
        "custos_pagos": round(resultado.custos_pagos, 2),
        "imposto_pago": round(resultado.imposto_pago, 2),
        "saltos_zerados": resultado.saltos_zerados,
        "patrimonio_final": round(float(carteira.iloc[-1]), 2),
    }
