from __future__ import annotations

import numpy as np
import pandas as pd

from pesquisa.dados import Base

PREGOES_NO_ANO = 252


def preco_e_retorno(base: Base) -> tuple[pd.DataFrame, pd.DataFrame]:
    preco = base.preco_ajustado.ffill()
    retorno = preco.pct_change(fill_method=None).mask(base.salto, 0.0)
    indice = (1 + retorno.fillna(0.0)).cumprod().where(preco.notna())
    return indice, retorno


def momento_risco(indice: pd.DataFrame, retorno: pd.DataFrame, pos: int, p: dict) -> pd.Series:
    janela, pulo = p["janela"], p["pulo"]
    if pos < janela:
        return pd.Series(dtype=float)
    acumulado = indice.iloc[pos - pulo] / indice.iloc[pos - janela] - 1
    volatilidade = retorno.iloc[pos - janela + 1 : pos + 1].std() * np.sqrt(PREGOES_NO_ANO)
    return (acumulado / volatilidade.where(volatilidade > 0)).dropna()


def distancia_media(indice: pd.DataFrame, retorno: pd.DataFrame, pos: int, p: dict) -> pd.Series:
    janela = p["janela"]
    if pos + 1 < janela:
        return pd.Series(dtype=float)
    trecho = indice.iloc[pos - janela + 1 : pos + 1]
    desvio = trecho.std()
    return ((indice.iloc[pos] - trecho.mean()) / desvio.where(desvio > 0)).dropna()


def inclinacao_r2(indice: pd.DataFrame, retorno: pd.DataFrame, pos: int, p: dict) -> pd.Series:
    janela = p["janela"]
    if pos + 1 < janela:
        return pd.Series(dtype=float)
    trecho = np.log(indice.iloc[pos - janela + 1 : pos + 1]).dropna(axis=1)
    if trecho.empty:
        return pd.Series(dtype=float)
    x = np.arange(janela, dtype=float)
    x -= x.mean()
    y = trecho.to_numpy() - trecho.to_numpy().mean(axis=0)
    covariancia = x @ y
    soma_y = (y**2).sum(axis=0)
    r2 = np.divide(covariancia**2, (x @ x) * soma_y, out=np.zeros_like(soma_y), where=soma_y > 0)
    return pd.Series(covariancia / (x @ x) * PREGOES_NO_ANO * r2, index=trecho.columns)
