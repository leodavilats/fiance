from __future__ import annotations

import pandas as pd

from pesquisa.dados import Base
from pesquisa.hipoteses import Hipotese, momento
from pesquisa.universo import JANELA_DE_VOLUME, VOLUME_MINIMO

_MERCADO: dict[int, pd.Series] = {}


def _mercado(base: Base) -> pd.Series:
    if id(base) in _MERCADO:
        return _MERCADO[id(base)]
    liquido = (
        base.volume.rolling(JANELA_DE_VOLUME, min_periods=JANELA_DE_VOLUME).median()
        >= VOLUME_MINIMO
    )
    retorno = base.retorno.where(liquido & ~base.salto)
    _MERCADO[id(base)] = (1 + retorno.mean(axis=1).fillna(0)).cumprod()
    return _MERCADO[id(base)]


def mercado_em_alta(base: Base, dia: pd.Timestamp, meses: int) -> bool:
    indice = _mercado(base).loc[:dia]
    fins = indice.groupby([indice.index.year, indice.index.month]).last().iloc[-meses:]
    return len(fins) == meses and indice.iloc[-1] > fins.mean()


def escolher(base: Base, dia: pd.Timestamp, parametros: dict) -> list[str]:
    if not mercado_em_alta(base, dia, parametros["meses_da_media"]):
        return []
    return momento.escolher(base, dia, parametros)


MOMENTO_TENDENCIA = Hipotese(
    nome="momento_tendencia",
    descricao=(
        "Momento 12–1 só com o mercado acima da média dos últimos 10 fins de mês; fora disso, CDI"
    ),
    escolher=escolher,
    parametros={"olhar": 252, "pular": 21, "quantidade": 20, "meses_da_media": 10},
)
