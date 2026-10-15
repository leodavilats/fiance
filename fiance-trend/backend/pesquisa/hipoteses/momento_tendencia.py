from __future__ import annotations

import pandas as pd

from pesquisa.dados import Base
from pesquisa.hipoteses import Hipotese, momento
from pesquisa.universo import JANELA_DE_VOLUME, VOLUME_MINIMO

# Guarda a base junto: o id de um objeto coletado volta em outro, e o índice viria da base errada.
_MERCADO: dict[int, tuple[Base, pd.Series]] = {}


def _mercado(base: Base) -> pd.Series:
    guardado = _MERCADO.get(id(base))
    if guardado is not None and guardado[0] is base:
        return guardado[1]
    liquido = (
        base.volume.rolling(JANELA_DE_VOLUME, min_periods=JANELA_DE_VOLUME).median()
        >= VOLUME_MINIMO
    )
    retorno = base.retorno.where(liquido & ~base.salto)
    indice = (1 + retorno.mean(axis=1).fillna(0)).cumprod()
    _MERCADO[id(base)] = (base, indice)
    return indice


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

MOMENTO_TENDENCIA_TRIMESTRAL = Hipotese(
    nome="momento_tendencia_trimestral",
    descricao="Momento com filtro de tendência, rebalanceado no fim de cada trimestre",
    escolher=escolher,
    parametros={**MOMENTO_TENDENCIA.parametros, "meses_entre_rebalanceamentos": 3},
)
