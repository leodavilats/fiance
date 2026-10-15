from __future__ import annotations

import pandas as pd

from pesquisa.dados import Base
from pesquisa.hipoteses import Hipotese
from pesquisa.hipoteses.momento_tendencia import mercado_em_alta
from pesquisa.hipoteses.valor_qualidade import um_papel_por_empresa
from pesquisa.universo import elegiveis


def rendimento(base: Base, dia: pd.Timestamp, papeis: list[str], janela: int) -> pd.Series:
    posicao = base.pregoes.get_loc(dia)
    pago = base.provento.iloc[posicao + 1 - janela : posicao + 1][papeis].fillna(0).sum()
    return (pago / base.preco_ajustado.loc[dia, papeis]).dropna()


def _empresas_com_proventos(base: Base) -> set[str]:
    pagaram = base.provento.fillna(0).sum() > 0
    return {papel.split(":")[0] for papel in pagaram[pagaram].index}


def escolher(base: Base, dia: pd.Timestamp, parametros: dict) -> list[str]:
    if not mercado_em_alta(base, dia, parametros["meses_da_media"]):
        return []
    # Empresa sem histórico de proventos na base é lacuna da B3 (a ALL), não rendimento zero.
    cobertas = _empresas_com_proventos(base)
    papeis = [
        p
        for p in um_papel_por_empresa(base, dia, elegiveis(base, dia))
        if p.split(":")[0] in cobertas
    ]
    if not papeis:
        return []
    taxa = rendimento(base, dia, papeis, parametros["janela"])
    return list(taxa[taxa > 0].sort_values(ascending=False).index[: parametros["quantidade"]])


DIVIDENDOS = Hipotese(
    nome="dividendos_tendencia",
    descricao="Os 20 de maior provento em 12 meses sobre o preço, só com o mercado em alta",
    escolher=escolher,
    parametros={"janela": 252, "quantidade": 20, "meses_da_media": 10},
)
