from __future__ import annotations

import math
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from pesquisa.dados import Base
from pesquisa.fundamentos import acoes_na_data
from pesquisa.motor import fins_de_mes
from pesquisa.periodos import Periodo
from pesquisa.universo import elegiveis

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend"))

from app.analysis import fair_price as modelo  # noqa: E402
from app.collectors.rates import FAIXAS, SELIC_AVERAGE_MONTHS  # noqa: E402
from app.collectors.universal import proventos_do_app, snapshot_do_pacote  # noqa: E402

MESES_A_FRENTE = 12
DIFERENCA_MINIMA = 0.03
T_MINIMO = 2.0
AMOSTRA_POR_GRUPO = 10
MESES_COM_AMOSTRA = 0.8
DEFASAGENS = 11
GRUPOS = ("abaixo", "dentro", "acima")


def _texto(valor) -> str | None:
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return None
    return str(valor)[:10]


def _numero(valor) -> float | None:
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return None
    return float(valor)


class Dados:
    def __init__(self, base: Base):
        fundamentos = base.calibracao["fundamento_app"].copy()
        fundamentos["data_entrega"] = pd.to_datetime(fundamentos["data_entrega"])
        self.fundamentos = dict(list(fundamentos.groupby("cnpj")))
        proventos = base.calibracao["provento"].copy()
        proventos["data_com"] = pd.to_datetime(proventos["data_com"])
        self.proventos = dict(list(proventos.groupby(["cnpj", "classe"])))
        selic = base.calibracao["selic_mensal"].copy()
        selic["data"] = pd.to_datetime(selic["data"])
        self.selic = selic.sort_values("data").set_index("data")["valor"].astype(float)


def juro_na_data(selic: pd.Series, dia: pd.Timestamp) -> modelo.ValuationRates | None:
    valores = [v for v in selic[selic.index <= dia].iloc[-SELIC_AVERAGE_MONTHS:] if
               FAIXAS["selic_anual"].accepts(v)]  # fmt: skip
    if len(valores) < SELIC_AVERAGE_MONTHS // 2:
        return None
    media = round(sum(valores) / len(valores), 2)
    return modelo.rates_for_valuation({"selic_media_10a": media, "source": "bcb"})


def pacote_na_data(base: Base, dados: Dados, papel: str, dia: pd.Timestamp) -> dict | None:
    cnpj, classe = papel.split(":")
    preco = base.preco.at[dia, papel]
    acoes = acoes_na_data(base.acoes, dia).get(cnpj) if base.acoes is not None else None
    if pd.isna(preco) or not acoes:
        return None

    sabidos = dados.fundamentos.get(cnpj)
    linhas = [] if sabidos is None else sabidos[sabidos["data_entrega"] <= dia].to_dict("records")
    preferencial = classe.startswith("PN")
    ativo = {
        "codigo": str(base.nomes.get(papel, papel)),
        "tipo": "stock",
        "classe": classe,
        "data": dia.date().isoformat(),
        "preco": float(preco),
        "preco_anterior": None,
        "maxima_52s": None,
        "minima_52s": None,
        "volume_medio": None,
        "nome": None,
        "setor": None,
        "cnpj": cnpj,
        "acoes_ordinarias": 0 if preferencial else int(acoes),
        "acoes_preferenciais": int(acoes) if preferencial else 0,
        "valor_patrimonial_cota": None,
        "referencia_cota": None,
        "proventos_12m": None,
    }
    return {
        "ativo": ativo,
        "irmaos": [
            {
                "codigo": ativo["codigo"],
                "classe": classe,
                "preco": float(preco),
                "volume_medio": 1.0,
            }
        ],  # fmt: skip
        "resultados": [
            {
                "tipo": r["tipo"],
                "data_referencia": _texto(r["data_referencia"]),
                "versao": int(r["versao"]),
                "fim_exercicio": _texto(r["fim_exercicio"]),
                "receita": _numero(r["receita"]),
                "lucro_controladores": _numero(r["lucro_controladores"]),
            }
            for r in linhas
        ],
        "balancos": [
            {
                "tipo": r["tipo"],
                "data_referencia": _texto(r["data_referencia"]),
                "versao": int(r["versao"]),
                "patrimonio_controladores": _numero(r["patrimonio_controladores"]),
                "divida_bruta": _numero(r["divida_bruta"]),
            }
            for r in linhas
            if _numero(r["patrimonio_controladores"]) is not None
        ],
    }


def proventos_na_data(dados: Dados, papel: str, dia: pd.Timestamp) -> list[dict]:
    cnpj, classe = papel.split(":")
    tabela = dados.proventos.get((cnpj, classe))
    if tabela is None:
        return []
    sabidos = tabela[tabela["data_com"] <= dia]
    return proventos_do_app(
        [
            {
                "data_com": _texto(r["data_com"]),
                "data_pagamento": _texto(r["data_pagamento"]),
                "valor": _numero(r["valor"]),
            }
            for r in sabidos.to_dict("records")
        ]
    )


def veredito(base: Base, dados: Dados, papel: str, dia: pd.Timestamp, juro) -> str | None:
    if papel.endswith(":UNT"):
        return None
    pacote = pacote_na_data(base, dados, papel, dia)
    if pacote is None:
        return None
    snap = snapshot_do_pacote(pacote, pacote["ativo"]["codigo"], "br_stock")
    if snap is None:
        return None
    entradas = modelo.compute_fair_price_inputs(
        price=snap.price,
        eps=snap.eps,
        book_value=snap.book_value,
        dividends=proventos_na_data(dados, papel, dia),
        asset_type="br_stock",
        pb_ratio=snap.pb_ratio,
        roe_pct=snap.roe,
        net_income_history=snap.net_income_history,
        equity_history=snap.equity_history,
        net_income_ttm=snap.net_income_ttm,
        rates=juro,
        reference=datetime.combine(dia.date(), datetime.min.time(), UTC),
        symbol=snap.symbol,
    )
    justo = modelo.fair_price_from_inputs(
        entradas, desired_yield=modelo.desired_yield_for("br_stock", None)
    )
    if justo.fair_low is None or justo.fair_high is None:
        return None
    if snap.price < justo.fair_low:
        return "abaixo"
    if snap.price > justo.fair_high:
        return "acima"
    return "dentro"


def _t_newey_west(serie: pd.Series, defasagens: int) -> float:
    x = serie.to_numpy() - serie.mean()
    n = len(x)
    variancia = (x @ x) / n
    for k in range(1, min(defasagens, n - 1) + 1):
        peso = 1 - k / (defasagens + 1)
        variancia += 2 * peso * (x[k:] @ x[:-k]) / n
    if variancia <= 0:
        return 0.0
    return float(serie.mean() / math.sqrt(variancia / n))


def avaliar(base: Base, periodo: Periodo) -> tuple[dict, list[dict]]:
    dados = Dados(base)
    fins = sorted(d for d in fins_de_mes(base.pregoes) if periodo.contem(d.date()))
    retorno = base.retorno.mask(base.salto, 0.0).fillna(0.0)

    meses = []
    for i, dia in enumerate(fins[:-MESES_A_FRENTE]):
        adiante_dia = fins[i + MESES_A_FRENTE]
        juro = juro_na_data(dados.selic, dia)
        if juro is None:
            continue
        pos, pos_adiante = base.pregoes.get_loc(dia), base.pregoes.get_loc(adiante_dia)
        grupos: dict[str, list[float]] = defaultdict(list)
        sem_faixa = 0
        for papel in elegiveis(base, dia):
            grupo = veredito(base, dados, papel, dia, juro)
            if grupo is None:
                sem_faixa += 1
                continue
            adiante = float((1 + retorno.iloc[pos + 1 : pos_adiante + 1][papel]).prod() - 1)
            grupos[grupo].append(adiante)
        mes = {"mes": dia.date().isoformat(), "sem_faixa": sem_faixa}
        for g in GRUPOS:
            mes[f"n_{g}"] = len(grupos[g])
            mes[g] = sum(grupos[g]) / len(grupos[g]) if grupos[g] else None
        meses.append(mes)
    return resumir(meses), meses


def resumir(meses: list[dict]) -> dict:
    tabela = pd.DataFrame(meses)
    if tabela.empty:
        return {"meses": 0, "passou": False}
    com_os_dois = tabela.dropna(subset=["abaixo", "acima"])
    diferenca = com_os_dois["abaixo"] - com_os_dois["acima"]
    t = _t_newey_west(diferenca, DEFASAGENS) if len(diferenca) > DEFASAGENS + 1 else 0.0
    medias = {g: float(tabela[g].mean()) if tabela[g].notna().any() else None for g in GRUPOS}
    em_ordem = None not in medias.values() and medias["abaixo"] > medias["dentro"] > medias["acima"]
    com_amostra = float(
        (
            (tabela["n_abaixo"] >= AMOSTRA_POR_GRUPO) & (tabela["n_acima"] >= AMOSTRA_POR_GRUPO)
        ).mean()
    )
    media_diferenca = float(diferenca.mean()) if len(diferenca) else 0.0
    passou = (
        media_diferenca >= DIFERENCA_MINIMA
        and t >= T_MINIMO
        and em_ordem
        and com_amostra >= MESES_COM_AMOSTRA
    )
    return {
        "meses": len(tabela),
        "de": tabela["mes"].iloc[0],
        "ate": tabela["mes"].iloc[-1],
        "abaixo": round(medias["abaixo"], 4) if medias["abaixo"] is not None else None,
        "dentro": round(medias["dentro"], 4) if medias["dentro"] is not None else None,
        "acima": round(medias["acima"], 4) if medias["acima"] is not None else None,
        "diferenca": round(media_diferenca, 4),
        "t_newey_west": round(t, 2),
        "em_ordem": bool(em_ordem),
        "meses_com_amostra": round(com_amostra, 3),
        "n_medio": {g: round(float(tabela[f"n_{g}"].mean()), 1) for g in GRUPOS},
        "sem_faixa_medio": round(float(tabela["sem_faixa"].mean()), 1),
        "passou": bool(passou),
    }
