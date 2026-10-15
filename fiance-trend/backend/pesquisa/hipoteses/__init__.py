from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd

from pesquisa.dados import Base

Escolher = Callable[[Base, pd.Timestamp, dict], list[str]]


@dataclass(frozen=True)
class Hipotese:
    nome: str
    descricao: str
    escolher: Escolher
    parametros: dict = field(default_factory=dict)
    congelada: bool = False


def todas() -> dict[str, Hipotese]:
    from pesquisa.hipoteses import (
        baixa_volatilidade,
        dividendos,
        mercado_tendencia,
        momento,
        momento_tendencia,
        valor_qualidade,
    )

    return {
        h.nome: h
        for h in (
            momento.MOMENTO_12_1,
            valor_qualidade.VALOR_QUALIDADE,
            momento_tendencia.MOMENTO_TENDENCIA,
            momento_tendencia.MOMENTO_TENDENCIA_TRIMESTRAL,
            baixa_volatilidade.BAIXA_VOLATILIDADE,
            dividendos.DIVIDENDOS,
            mercado_tendencia.MERCADO_TENDENCIA,
            mercado_tendencia.ETF_TENDENCIA,
        )
    }
