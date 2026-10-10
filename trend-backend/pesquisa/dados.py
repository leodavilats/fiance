from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class Base:
    """O mercado em tabelas largas: uma linha por pregão, uma coluna por papel."""

    retorno: pd.DataFrame
    preco_ajustado: pd.DataFrame
    preco: pd.DataFrame
    volume: pd.DataFrame
    salto: pd.DataFrame
    cdi: pd.Series
    nomes: pd.Series
    retrato: str

    @property
    def pregoes(self) -> pd.DatetimeIndex:
        return self.retorno.index


def montar(serie: pd.DataFrame, cdi: pd.DataFrame, retrato: str) -> Base:
    serie = serie.assign(
        papel=serie["cnpj"] + ":" + serie["classe"], data=pd.to_datetime(serie["data"])
    )

    def largo(coluna: str) -> pd.DataFrame:
        return serie.pivot(index="data", columns="papel", values=coluna).sort_index()

    salto = largo("salto_sem_evento")
    taxa = cdi.assign(data=pd.to_datetime(cdi["data"])).set_index("data")["valor"].astype(float)
    pregoes = salto.index
    return Base(
        retorno=largo("retorno_total").astype(float),
        preco_ajustado=largo("fechamento_ajustado").astype(float),
        preco=largo("fechamento").astype(float),
        volume=largo("volume").astype(float),
        salto=salto.astype("boolean").fillna(False).astype(bool),
        cdi=(taxa / 100).reindex(pregoes).fillna(0.0),
        nomes=serie.sort_values("data").groupby("papel")["codigo"].last(),
        retrato=retrato,
    )
