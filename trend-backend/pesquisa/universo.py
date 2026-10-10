from __future__ import annotations

import pandas as pd

from pesquisa.dados import Base

VOLUME_MINIMO = 5_000_000
PRECO_MINIMO = 1.0
HISTORIA_MINIMA = 252
JANELA_DE_VOLUME = 63
JANELA_DE_SALTO = 252


def elegiveis(base: Base, dia: pd.Timestamp) -> list[str]:
    posicao = base.pregoes.get_loc(dia)
    if posicao + 1 < HISTORIA_MINIMA:
        return []

    preco_hoje = base.preco.iloc[posicao]
    negociou_hoje = preco_hoje.notna()
    historia = base.preco.iloc[: posicao + 1].notna().sum() >= HISTORIA_MINIMA
    volume = base.volume.iloc[posicao + 1 - JANELA_DE_VOLUME : posicao + 1].median()
    salto = base.salto.iloc[posicao + 1 - JANELA_DE_SALTO : posicao + 1].any()

    ok = (
        negociou_hoje & historia & (volume >= VOLUME_MINIMO) & (preco_hoje >= PRECO_MINIMO) & ~salto
    )
    return sorted(ok[ok].index)
