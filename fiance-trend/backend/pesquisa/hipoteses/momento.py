from __future__ import annotations

import pandas as pd

from pesquisa.dados import Base
from pesquisa.hipoteses import Hipotese
from pesquisa.universo import elegiveis


def pontuar(base: Base, dia: pd.Timestamp, olhar: int, pular: int) -> pd.Series:
    posicao = base.pregoes.get_loc(dia)
    if posicao < olhar:
        return pd.Series(dtype=float)
    fim = base.preco_ajustado.iloc[posicao - pular]
    inicio = base.preco_ajustado.iloc[posicao - olhar]
    return (fim / inicio - 1).dropna()


def escolher(base: Base, dia: pd.Timestamp, parametros: dict) -> list[str]:
    candidatos = elegiveis(base, dia)
    pontos = (
        pontuar(base, dia, parametros["olhar"], parametros["pular"]).reindex(candidatos).dropna()
    )
    return list(pontos.sort_values(ascending=False).index[: parametros["quantidade"]])


MOMENTO_12_1 = Hipotese(
    nome="momento_12_1",
    descricao="Retorno de 12 meses ignorando o último; compra os 20 maiores",
    escolher=escolher,
    parametros={"olhar": 252, "pular": 21, "quantidade": 20},
)
