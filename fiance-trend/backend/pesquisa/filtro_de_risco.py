from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from pesquisa import registro
from pesquisa.dados import Base
from pesquisa.hipoteses.mercado_tendencia import ETF_TENDENCIA, garantir_etf
from pesquisa.metricas import resumir
from pesquisa.motor import Resultado, fins_de_mes, simular
from pesquisa.periodos import VALIDACAO

ARQUIVO = Path(__file__).resolve().parents[1] / "registro_filtro.jsonl"
ASSINATURA_DA_VARIACAO_8 = "1be95b0b042a"
FRACAO_MAXIMA_DA_QUEDA = 2 / 3
CUSTO_MAXIMO_AO_ANO = -0.03


class Recusado(RuntimeError):
    pass


def ler(arquivo: Path = ARQUIVO) -> list[dict]:
    if not arquivo.exists():
        return []
    return [json.loads(x) for x in arquivo.read_text(encoding="utf-8").splitlines() if x]


def conferir(forcar: bool, arquivo: Path = ARQUIVO) -> None:
    if registro.assinatura(ETF_TENDENCIA) != ASSINATURA_DA_VARIACAO_8:
        raise Recusado("A hipótese mudou desde a variação 8: o protocolo exige a mesma assinatura.")
    if ler(arquivo) and not forcar:
        raise Recusado("A validação já foi aberta para esta pergunta: o protocolo não repete.")


def quedas(patrimonio: pd.Series) -> list[float]:
    topo = patrimonio.cummax()
    queda = patrimonio / topo - 1
    episodio = (patrimonio >= topo).cumsum()
    return sorted(float(q) for q in queda.groupby(episodio).min() if q < 0)


def meses_fora(resultado: Resultado) -> int:
    return sum(1 for carteira in resultado.carteiras.values() if not carteira)


def _medidas(resultado: Resultado) -> dict:
    resumo = resumir(resultado)
    piores = quedas(resultado.patrimonio)
    resumo["segunda_pior_queda"] = round(piores[1], 4) if len(piores) > 1 else None
    resumo["meses_fora_do_mercado"] = meses_fora(resultado)
    resumo["meses"] = len(resultado.carteiras)
    return resumo


def julgar(filtrado: dict, comprado: dict) -> dict:
    corta = abs(filtrado["pior_queda"]) <= FRACAO_MAXIMA_DA_QUEDA * abs(comprado["pior_queda"])
    menos_volatil = filtrado["volatilidade_anual"] < comprado["volatilidade_anual"]
    diferenca = round(filtrado["retorno_anual"] - comprado["retorno_anual"], 4)
    paga = diferenca >= CUSTO_MAXIMO_AO_ANO
    return {
        "corta_a_queda": bool(corta),
        "menos_volatil": bool(menos_volatil),
        "diferenca_de_retorno_anual": diferenca,
        "custo_aceitavel": bool(paga),
        "confirmado": bool(corta and menos_volatil and paga),
    }


def rodar(base: Base) -> dict:
    nome = garantir_etf(base, ETF_TENDENCIA.parametros["etf"])

    def sempre(dia: pd.Timestamp) -> list[str]:
        return [] if pd.isna(base.preco.loc[dia, nome]) else [nome]

    filtrado = simular(
        base, VALIDACAO, lambda dia: ETF_TENDENCIA.escolher(base, dia, ETF_TENDENCIA.parametros)
    )
    comprado = simular(base, VALIDACAO, sempre)
    medidas = {"filtrado": _medidas(filtrado), "comprado_sempre": _medidas(comprado)}
    fins = sorted(d for d in fins_de_mes(base.pregoes) if VALIDACAO.contem(d.date()))
    return {
        "periodo": VALIDACAO.nome,
        "de": fins[0].date().isoformat() if fins else None,
        "ate": fins[-1].date().isoformat() if fins else None,
        "assinatura": ASSINATURA_DA_VARIACAO_8,
        **medidas,
        **julgar(medidas["filtrado"], medidas["comprado_sempre"]),
    }


def anotar(retrato: str, resumo: dict, forcado: bool, arquivo: Path = ARQUIVO) -> dict:
    linha = {
        "quando": datetime.now(UTC).isoformat(timespec="seconds"),
        "retrato": retrato,
        "forcado": forcado,
        "resumo": resumo,
    }
    with arquivo.open("a", encoding="utf-8") as saida:
        saida.write(json.dumps(linha, ensure_ascii=False) + "\n")
    return linha
