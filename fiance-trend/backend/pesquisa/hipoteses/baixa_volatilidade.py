from __future__ import annotations

import pandas as pd

from pesquisa.dados import Base
from pesquisa.hipoteses import Hipotese
from pesquisa.hipoteses.momento_tendencia import mercado_em_alta
from pesquisa.hipoteses.valor_qualidade import um_papel_por_empresa
from pesquisa.universo import elegiveis


def volatilidade(
    base: Base, dia: pd.Timestamp, papeis: list[str], janela: int, minimo: int
) -> pd.Series:
    posicao = base.pregoes.get_loc(dia)
    trecho = base.retorno.iloc[posicao + 1 - janela : posicao + 1][papeis]
    trecho = trecho.where(~base.salto.iloc[posicao + 1 - janela : posicao + 1][papeis])
    desvio = trecho.std()
    return desvio[trecho.count() >= minimo]


def escolher(base: Base, dia: pd.Timestamp, parametros: dict) -> list[str]:
    if not mercado_em_alta(base, dia, parametros["meses_da_media"]):
        return []
    papeis = um_papel_por_empresa(base, dia, elegiveis(base, dia))
    if not papeis:
        return []
    desvio = volatilidade(base, dia, papeis, parametros["janela"], parametros["pregoes_minimos"])
    return list(desvio.sort_values().index[: parametros["quantidade"]])


BAIXA_VOLATILIDADE = Hipotese(
    nome="baixa_volatilidade_tendencia",
    descricao=(
        "Os 20 de menor volatilidade em 12 meses, só com o mercado acima da média de 10 fins de mês"
    ),
    escolher=escolher,
    parametros={"janela": 252, "pregoes_minimos": 200, "quantidade": 20, "meses_da_media": 10},
)
