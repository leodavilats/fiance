from __future__ import annotations

from dataclasses import dataclass, field

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
    provento: pd.DataFrame | None = None
    etf: pd.DataFrame | None = None
    fundamentos: pd.DataFrame | None = None
    acoes: pd.DataFrame | None = None
    fii: Base | None = None
    calibracao: dict[str, pd.DataFrame] = field(default_factory=dict)

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
        provento=largo("provento").astype(float) if "provento" in serie else None,
    )


def acrescentar_ativo(base: Base, nome: str, retorno: pd.Series, preco: pd.Series) -> None:
    if nome in base.retorno.columns:
        return
    base.retorno = pd.concat([base.retorno, retorno.rename(nome)], axis=1)
    base.preco = pd.concat([base.preco, preco.rename(nome)], axis=1)
    base.preco_ajustado = pd.concat([base.preco_ajustado, preco.rename(nome)], axis=1)
    volume = pd.Series(float("inf"), index=base.pregoes, name=nome)
    base.volume = pd.concat([base.volume, volume], axis=1)
    base.salto = pd.concat([base.salto, pd.Series(False, index=base.pregoes, name=nome)], axis=1)
