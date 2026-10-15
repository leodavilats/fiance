from __future__ import annotations

import pandas as pd

from pesquisa.dados import Base, acrescentar_ativo
from pesquisa.hipoteses import Hipotese
from pesquisa.hipoteses.momento_tendencia import _mercado, mercado_em_alta

# A série não tem Ibovespa nem ETF: o mercado é a média diária, em pesos iguais, dos papéis líquidos,
# negociada como um ativo só. Aproxima um ETF; o giro interno do índice não paga custo.
MERCADO = "mercado:sintetico"


def garantir_mercado(base: Base) -> None:
    indice = _mercado(base)
    acrescentar_ativo(base, MERCADO, indice.pct_change(), indice * 100)


def escolher(base: Base, dia: pd.Timestamp, parametros: dict) -> list[str]:
    garantir_mercado(base)
    return [MERCADO] if mercado_em_alta(base, dia, parametros["meses_da_media"]) else []


MERCADO_TENDENCIA = Hipotese(
    nome="mercado_tendencia",
    descricao="O mercado inteiro, em pesos iguais, só acima da média de 10 fins de mês; senão, CDI",
    escolher=escolher,
    parametros={"meses_da_media": 10},
)


def garantir_etf(base: Base, codigo: str) -> str:
    nome = f"etf:{codigo}"
    serie = base.etf[base.etf["codigo"] == codigo].set_index("data")
    preco = (serie["fechamento"] / serie["fator_cotacao"]).reindex(base.pregoes)
    acrescentar_ativo(base, nome, preco.pct_change(fill_method=None), preco)
    return nome


def escolher_etf(base: Base, dia: pd.Timestamp, parametros: dict) -> list[str]:
    nome = garantir_etf(base, parametros["etf"])
    if pd.isna(base.preco.loc[dia, nome]):
        return []
    return [nome] if mercado_em_alta(base, dia, parametros["meses_da_media"]) else []


ETF_TENDENCIA = Hipotese(
    nome="etf_tendencia",
    descricao="PIBB11 só com o mercado acima da média de 10 fins de mês; senão, CDI",
    escolher=escolher_etf,
    parametros={"etf": "PIBB11", "meses_da_media": 10},
)
