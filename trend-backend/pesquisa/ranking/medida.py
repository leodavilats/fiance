from __future__ import annotations

import math

import pandas as pd

from pesquisa.dados import Base
from pesquisa.motor import fins_de_mes
from pesquisa.periodos import Periodo
from pesquisa.ranking import Classe, Sinal
from pesquisa.ranking.sinais import preco_e_retorno
from pesquisa.universo import elegiveis

MINIMO_DE_ATIVOS = 20
CUSTO_POR_TROCA = 0.005
IC_MINIMO = 0.03
T_MINIMO = 2.0
ACERTO_MINIMO = 0.55


def _correlacao_de_postos(a: pd.Series, b: pd.Series) -> float:
    return float(a.rank().corr(b.rank()))


def _giro(atual: set[str], anterior: set[str] | None) -> float:
    if anterior is None:
        return 1.0
    return len(atual - anterior) / len(atual)


def avaliar(base: Base, periodo: Periodo, sinal: Sinal, classe: Classe) -> tuple[dict, list[dict]]:
    inicio = max(periodo.inicio, classe.desde)
    fins = sorted(
        d for d in fins_de_mes(base.pregoes) if inicio <= d.date() and periodo.contem(d.date())
    )
    indice, retorno_preco = preco_e_retorno(base)
    retorno_total = base.retorno.mask(base.salto, 0.0).fillna(0.0)

    meses, topo_antes, fundo_antes = [], None, None
    for dia, seguinte in zip(fins, fins[1:], strict=False):
        pos, pos_seguinte = base.pregoes.get_loc(dia), base.pregoes.get_loc(seguinte)
        universo = elegiveis(base, dia, classe.volume_minimo)
        valores = sinal.calcular(indice, retorno_preco, pos, sinal.parametros).reindex(universo)
        negocia_depois = base.preco.iloc[pos_seguinte].reindex(universo).notna()
        validos = valores[negocia_depois].dropna()
        if len(validos) < MINIMO_DE_ATIVOS:
            continue
        adiante = (1 + retorno_total.iloc[pos + 1 : pos_seguinte + 1][validos.index]).prod() - 1
        k = len(validos) // 5
        ordem = validos.sort_values()
        topo, fundo = set(ordem.index[-k:]), set(ordem.index[:k])
        retorno_topo = float(adiante[list(topo)].mean())
        retorno_fundo = float(adiante[list(fundo)].mean())
        giro = _giro(topo, topo_antes) + _giro(fundo, fundo_antes)
        meses.append(
            {
                "mes": dia.date().isoformat(),
                "ativos": len(validos),
                "saidas": int((~negocia_depois).sum()),
                "ic": _correlacao_de_postos(validos, adiante),
                "topo": retorno_topo,
                "fundo": retorno_fundo,
                "giro": giro,
                "liquida": retorno_topo - retorno_fundo - CUSTO_POR_TROCA * giro,
                "topo_nomes": sorted(str(base.nomes.get(p, p)) for p in topo),
            }
        )
        topo_antes, fundo_antes = topo, fundo
    return resumir(meses), meses


def resumir(meses: list[dict]) -> dict:
    if len(meses) < 2:
        return {"meses": len(meses), "passou": False}
    tabela = pd.DataFrame(meses)
    ic = tabela["ic"]
    desvio = ic.std(ddof=1)
    t = ic.mean() / (desvio / math.sqrt(len(ic))) if desvio > 0 else 0.0
    acerto = float((tabela["topo"] > tabela["fundo"]).mean())
    liquida = float(tabela["liquida"].mean() * 12)
    passou = ic.mean() >= IC_MINIMO and t >= T_MINIMO and acerto >= ACERTO_MINIMO and liquida > 0
    return {
        "meses": len(tabela),
        "de": tabela["mes"].iloc[0],
        "ate": tabela["mes"].iloc[-1],
        "ativos_medio": round(float(tabela["ativos"].mean()), 1),
        "saidas": int(tabela["saidas"].sum()),
        "ic": round(float(ic.mean()), 4),
        "t": round(float(t), 2),
        "acerto_topo": round(acerto, 3),
        "diferenca_bruta_ano": round(float((tabela["topo"] - tabela["fundo"]).mean() * 12), 4),
        "diferenca_liquida_ano": round(liquida, 4),
        "giro_medio": round(float(tabela["giro"].mean()), 3),
        "passou": bool(passou),
    }
