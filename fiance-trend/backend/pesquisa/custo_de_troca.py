from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from pesquisa.dados import Base
from pesquisa.motor import fins_de_mes
from pesquisa.universo import JANELA_DE_VOLUME

ARQUIVO = Path(__file__).resolve().parents[1] / "registro_custo.jsonl"
DE, ATE = pd.Timestamp("2005-01-01"), pd.Timestamp("2025-12-31")
CUSTO_DAS_PESQUISAS = 0.0025
FAIXA_DA_REGRA = "5 a 20 mi"

# Tarifa de negociação e liquidação da B3 para pessoa física (fora do day trade), por lado.
# Fonte e vigência no resultado do protocolo (docs/pesquisa/estudos/custo-de-troca.md).
TARIFA_B3 = 0.00031

FAIXAS = (
    ("abaixo de 1 mi", 0.0, 1e6),
    ("1 a 5 mi", 1e6, 5e6),
    ("5 a 20 mi", 5e6, 20e6),
    ("acima de 20 mi", 20e6, math.inf),
)

_K = 3 - 2 * math.sqrt(2)


class Recusado(RuntimeError):
    pass


def ler(arquivo: Path = ARQUIVO) -> list[dict]:
    if not arquivo.exists():
        return []
    return [json.loads(x) for x in arquivo.read_text(encoding="utf-8").splitlines() if x]


def conferir(forcar: bool, arquivo: Path = ARQUIVO) -> None:
    if ler(arquivo) and not forcar:
        raise Recusado("O custo de troca já foi medido: o protocolo não repete sem --forcar.")


def corwin_schultz(
    maxima: pd.DataFrame, minima: pd.DataFrame, valido: pd.DataFrame
) -> pd.DataFrame:
    h1, l1 = maxima, minima
    h2, l2 = maxima.shift(-1), minima.shift(-1)
    beta = np.log(h1 / l1) ** 2 + np.log(h2 / l2) ** 2
    gama = np.log(np.maximum(h1, h2) / np.minimum(l1, l2)) ** 2
    alfa = (np.sqrt(2 * beta) - np.sqrt(beta)) / _K - np.sqrt(gama / _K)
    spread = (2 * (np.exp(alfa) - 1) / (1 + np.exp(alfa))).clip(lower=0)
    return spread.where(valido & valido.shift(-1, fill_value=False))


def _largo(tabela: pd.DataFrame, coluna: str, base: Base) -> pd.DataFrame:
    tabela = tabela.assign(
        papel=tabela["cnpj"].astype(str) + ":" + tabela["classe"].astype(str),
        data=pd.to_datetime(tabela["data"]),
    )
    largo = tabela.pivot_table(index="data", columns="papel", values=coluna, aggfunc="first")
    return largo.astype(float).reindex(index=base.pregoes, columns=base.preco.columns)


def dias_validos(
    base: Base, maxima: pd.DataFrame, minima: pd.DataFrame, media: pd.DataFrame
) -> pd.DataFrame:
    preco = base.preco
    dentro = (
        (minima > 0)
        & (maxima >= minima)
        & (preco >= minima)
        & (preco <= maxima)
        & (media.isna() | ((media >= minima) & (media <= maxima)))
    )
    fator = base.preco_ajustado / preco
    sem_evento_ate_o_proximo = (fator.shift(-1) / fator - 1).abs() < 1e-6
    return dentro & ~base.salto & sem_evento_ate_o_proximo


def _faixa(volume: float) -> str | None:
    if pd.isna(volume):
        return None
    return next(nome for nome, de, ate in FAIXAS if de <= volume < ate)


def medir(base: Base, extremos: pd.DataFrame) -> pd.DataFrame:
    maxima = _largo(extremos, "maxima", base)
    minima = _largo(extremos, "minima", base)
    media = _largo(extremos, "media", base)
    spread = corwin_schultz(maxima, minima, dias_validos(base, maxima, minima, media))
    volume = base.volume.rolling(JANELA_DE_VOLUME, min_periods=JANELA_DE_VOLUME).median()

    linhas = []
    meses = base.pregoes.to_period("M")
    for dia in sorted(fins_de_mes(base.pregoes)):
        if not (DE <= dia <= ATE):
            continue
        do_mes = spread[meses == dia.to_period("M")]
        medio = do_mes.mean()
        dias = do_mes.notna().sum()
        for papel in medio[medio.notna()].index:
            faixa = _faixa(volume.at[dia, papel])
            if faixa is not None:
                linhas.append((dia.year, faixa, papel, float(medio[papel]), int(dias[papel])))
    return pd.DataFrame(linhas, columns=["ano", "faixa", "papel", "spread", "dias"])


def resumir(medidas: dict[str, pd.DataFrame]) -> dict:
    resumo: dict = {"tarifa_b3_por_lado": TARIFA_B3, "classes": {}}
    for classe, tabela in medidas.items():
        if tabela.empty:
            resumo["classes"][classe] = {"papeis_mes": 0}
            continue
        por_faixa = {}
        for nome, _, _ in FAIXAS:
            da_faixa = tabela[tabela["faixa"] == nome]
            if da_faixa.empty:
                continue
            spread = float(da_faixa["spread"].median())
            por_faixa[nome] = {
                "papeis_mes": len(da_faixa),
                "spread_mediano": round(spread, 5),
                "custo_por_lado": round(spread / 2 + TARIFA_B3, 5),
                "por_ano": {
                    int(ano): round(float(g["spread"].median()) / 2 + TARIFA_B3, 5)
                    for ano, g in da_faixa.groupby("ano")
                },
            }
        acima_da_regra = tabela[tabela["faixa"].isin([FAIXA_DA_REGRA, FAIXAS[-1][0]])]
        custo_regra = (
            round(float(acima_da_regra["spread"].median()) / 2 + TARIFA_B3, 5)
            if not acima_da_regra.empty
            else None
        )
        resumo["classes"][classe] = {
            "papeis_mes": len(tabela),
            "faixas": por_faixa,
            "custo_por_lado_acima_de_5_mi": custo_regra,
            "passa_do_custo_das_pesquisas": custo_regra is not None
            and custo_regra > CUSTO_DAS_PESQUISAS,
        }
    return resumo


def rodar(base: Base) -> tuple[dict, dict[str, pd.DataFrame]]:
    if "extremos_acao" not in base.extras:
        raise Recusado("O retrato não tem máxima e mínima: tire um retrato novo.")
    medidas = {"acao": medir(base, base.extras["extremos_acao"])}
    if base.fii is not None and "extremos_fii" in base.extras:
        medidas["fii"] = medir(base.fii, base.extras["extremos_fii"])
    return resumir(medidas), medidas


def anotar(retrato: str, resumo: dict, forcado: bool, arquivo: Path = ARQUIVO) -> dict:
    registro = {
        "quando": datetime.now(UTC).isoformat(timespec="seconds"),
        "retrato": retrato,
        "forcado": forcado,
        "resumo": resumo,
    }
    with arquivo.open("a", encoding="utf-8") as saida:
        saida.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return registro
