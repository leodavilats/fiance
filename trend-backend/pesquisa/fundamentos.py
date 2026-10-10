from __future__ import annotations

import pandas as pd

DEFASAGEM_MAXIMA = pd.Timedelta(days=460)


def _ultima_versao(tabela: pd.DataFrame, chave: list[str]) -> pd.DataFrame:
    return tabela.sort_values("versao").drop_duplicates(chave, keep="last")


def _datas(tabela: pd.DataFrame, *colunas: str) -> pd.DataFrame:
    return tabela.assign(
        cnpj=tabela["cnpj"].astype(str).str.zfill(14),
        **{c: pd.to_datetime(tabela[c]) for c in colunas},
    )


def preparar(resultado: pd.DataFrame, balanco: pd.DataFrame) -> pd.DataFrame:
    resultado = _datas(resultado, "data_referencia", "fim_exercicio", "disponivel_em")
    resultado = _ultima_versao(resultado, ["cnpj", "tipo", "data_referencia"])
    acumulado = (
        resultado.sort_values("tipo")
        .drop_duplicates(["cnpj", "fim_exercicio"], keep="first")
        .rename(columns={"lucro_controladores": "lucro_no_ano"})
    )

    anterior = acumulado[["cnpj", "fim_exercicio", "lucro_no_ano"]]
    doze = acumulado.assign(
        fim_ano_anterior=pd.to_datetime(acumulado["fim_exercicio"].dt.year - 1, format="%Y")
        + pd.offsets.YearEnd(0),
        mesmo_ponto_ano_anterior=acumulado["fim_exercicio"] - pd.DateOffset(years=1),
    )
    doze = doze.merge(
        anterior.rename(
            columns={"fim_exercicio": "fim_ano_anterior", "lucro_no_ano": "anual_anterior"}
        ),
        on=["cnpj", "fim_ano_anterior"],
        how="left",
    ).merge(
        anterior.rename(
            columns={"fim_exercicio": "mesmo_ponto_ano_anterior", "lucro_no_ano": "ponto_anterior"}
        ),
        on=["cnpj", "mesmo_ponto_ano_anterior"],
        how="left",
    )
    fim_de_ano = (doze["fim_exercicio"].dt.month == 12) & (doze["fim_exercicio"].dt.day == 31)
    doze["lucro_12m"] = doze["lucro_no_ano"].where(
        fim_de_ano, doze["lucro_no_ano"] + doze["anual_anterior"] - doze["ponto_anterior"]
    )

    balanco = _ultima_versao(
        _datas(balanco, "data_referencia"), ["cnpj", "tipo", "data_referencia"]
    )
    balanco = balanco.groupby(["cnpj", "data_referencia"], as_index=False)[
        "patrimonio_controladores"
    ].last()

    tabela = (
        doze[["cnpj", "data_referencia", "disponivel_em", "lucro_12m"]]
        .merge(balanco, on=["cnpj", "data_referencia"], how="left")
        .rename(columns={"patrimonio_controladores": "patrimonio"})
    )
    return tabela.sort_values(["cnpj", "disponivel_em", "data_referencia"]).reset_index(drop=True)


def na_data(fundamentos: pd.DataFrame, dia: pd.Timestamp) -> pd.DataFrame:
    sabido = fundamentos[fundamentos["disponivel_em"] <= dia]
    ultimo = sabido.groupby("cnpj").last()
    return ultimo[ultimo["data_referencia"] >= dia - DEFASAGEM_MAXIMA]


def preparar_acoes(composicao: pd.DataFrame, capital: pd.DataFrame) -> pd.DataFrame:
    composicao = _datas(composicao, "data_referencia")
    trimestral = pd.DataFrame(
        {
            "cnpj": composicao["cnpj"],
            "data": composicao["data_referencia"],
            "acoes": composicao["acoes_total"] - composicao["tesouraria_total"].fillna(0),
        }
    )
    capital = _datas(capital, "data_aprovacao", "data_referencia")
    aprovado = (
        capital.sort_values(["data_referencia", "versao"])
        .drop_duplicates(["cnpj", "data_aprovacao"], keep="last")
        .rename(columns={"data_aprovacao": "data", "acoes_total": "acoes"})[
            ["cnpj", "data", "acoes"]
        ]
    )
    tabela = pd.concat([t for t in (aprovado, trimestral) if not t.empty]).dropna()
    tabela = tabela[tabela["acoes"] > 0].drop_duplicates(["cnpj", "data"], keep="last")
    tabela = tabela.sort_values(["cnpj", "data"]).reset_index(drop=True)
    return tabela[~_destoa_dos_vizinhos(tabela)].reset_index(drop=True)


# O Banco do Brasil declara 286 milhões de ações no FRE de 2015, um décimo do que tem antes e depois.
# Desdobramento muda a quantidade de vez; erro de digitação volta no registro seguinte.
SALTO_DE_DIGITACAO = 3.0


def _destoa_dos_vizinhos(tabela: pd.DataFrame) -> pd.Series:
    por_empresa = tabela.groupby("cnpj")["acoes"]
    anterior, seguinte = por_empresa.shift(1), por_empresa.shift(-1)
    contra_anterior = tabela["acoes"] / anterior
    contra_seguinte = tabela["acoes"] / seguinte
    vizinhos_concordam = (anterior / seguinte).between(1 / SALTO_DE_DIGITACAO, SALTO_DE_DIGITACAO)
    acima = (contra_anterior > SALTO_DE_DIGITACAO) & (contra_seguinte > SALTO_DE_DIGITACAO)
    abaixo = (contra_anterior < 1 / SALTO_DE_DIGITACAO) & (contra_seguinte < 1 / SALTO_DE_DIGITACAO)
    return vizinhos_concordam & (acima | abaixo)


def acoes_na_data(acoes: pd.DataFrame, dia: pd.Timestamp) -> pd.Series:
    return acoes[acoes["data"] <= dia].groupby("cnpj")["acoes"].last()
