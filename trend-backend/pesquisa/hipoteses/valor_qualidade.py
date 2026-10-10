from __future__ import annotations

import numpy as np
import pandas as pd

from pesquisa.dados import Base
from pesquisa.fundamentos import acoes_na_data, na_data
from pesquisa.hipoteses import Hipotese
from pesquisa.universo import JANELA_DE_VOLUME, elegiveis

# A CVM recebe a quantidade de ações em unidades diferentes conforme a empresa (a Gafisa declara em
# milhares). Valor de mercado abaixo de 2% do patrimônio não existe na prática: é a unidade.
PRECO_SOBRE_PATRIMONIO_MINIMO = 0.02


def um_papel_por_empresa(base: Base, dia: pd.Timestamp, papeis: list[str]) -> list[str]:
    if not papeis:
        return []
    posicao = base.pregoes.get_loc(dia)
    volume = base.volume.iloc[posicao + 1 - JANELA_DE_VOLUME : posicao + 1][papeis].median()
    empresas = pd.Series(volume.index.str.split(":").str[0], index=volume.index)
    return sorted(volume.groupby(empresas).idxmax())


def pontuar(base: Base, dia: pd.Timestamp, papeis: list[str]) -> pd.DataFrame:
    fundamentos = na_data(base.fundamentos, dia)
    tabela = pd.DataFrame(index=papeis)
    tabela["cnpj"] = tabela.index.str.split(":").str[0]
    tabela = tabela.join(fundamentos, on="cnpj")
    tabela["acoes"] = tabela["cnpj"].map(acoes_na_data(base.acoes, dia))
    tabela["preco"] = base.preco.loc[dia, papeis]

    valor = tabela["preco"] * tabela["acoes"]
    em_milhares = valor < tabela["patrimonio"] * PRECO_SOBRE_PATRIMONIO_MINIMO
    valor = valor.where(~em_milhares, valor * 1000)

    tabela["roe"] = tabela["lucro_12m"] / tabela["patrimonio"].where(tabela["patrimonio"] > 0)
    tabela["lucro_sobre_valor"] = tabela["lucro_12m"] / valor
    return tabela.replace([np.inf, -np.inf], np.nan)


def escolher(base: Base, dia: pd.Timestamp, parametros: dict) -> list[str]:
    papeis = um_papel_por_empresa(base, dia, elegiveis(base, dia))
    tabela = pontuar(base, dia, papeis).dropna(subset=["roe", "lucro_sobre_valor"])
    tabela = tabela[(tabela["lucro_12m"] > 0) & (tabela["roe"] >= parametros["roe_minimo"])]
    melhores = tabela.sort_values("lucro_sobre_valor", ascending=False)
    return list(melhores.index[: parametros["quantidade"]])


VALOR_QUALIDADE = Hipotese(
    nome="valor_qualidade",
    descricao="Lucro de 12 meses sobre valor de mercado, entre os de ROE ≥ 15%; compra os 20 maiores",
    escolher=escolher,
    parametros={"roe_minimo": 0.15, "quantidade": 20},
)
