from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from pesquisa.dados import Base
from pesquisa.periodos import Periodo


@dataclass(frozen=True)
class Custos:
    por_lado: float = 0.0025
    imposto: float = 0.15


@dataclass
class Posicao:
    valor: float
    custo: float


@dataclass
class Resultado:
    patrimonio: pd.Series
    cdi: pd.Series
    giro: list[float] = field(default_factory=list)
    custos_pagos: float = 0.0
    imposto_pago: float = 0.0
    saltos_zerados: int = 0
    carteiras: dict[pd.Timestamp, list[str]] = field(default_factory=dict)


def fins_de_mes(pregoes: pd.DatetimeIndex) -> set[pd.Timestamp]:
    serie = pd.Series(pregoes, index=pregoes)
    return set(serie.groupby([pregoes.year, pregoes.month]).max())


def simular(
    base: Base,
    periodo: Periodo,
    escolher: Callable[[pd.Timestamp], list[str]],
    custos: Custos = Custos(),
    inicial: float = 100_000.0,
) -> Resultado:
    pregoes = base.pregoes[
        (base.pregoes >= pd.Timestamp(periodo.inicio))
        & ((base.pregoes <= pd.Timestamp(periodo.fim)) if periodo.fim else True)
    ]
    rebalancear = fins_de_mes(pregoes)

    posicoes: dict[str, Posicao] = {}
    caixa = inicial
    prejuizo = 0.0
    resultado = Resultado(patrimonio=pd.Series(dtype=float), cdi=pd.Series(dtype=float))
    patrimonio, referencia = [], []
    cdi_acumulado = inicial

    for dia in pregoes:
        retornos, saltos = base.retorno.loc[dia], base.salto.loc[dia]
        for papel, posicao in posicoes.items():
            r = retornos.get(papel, np.nan)
            if saltos.get(papel, False):
                resultado.saltos_zerados += 1
            elif not np.isnan(r):
                posicao.valor *= 1 + r
        caixa *= 1 + base.cdi.loc[dia]
        cdi_acumulado *= 1 + base.cdi.loc[dia]

        if dia in rebalancear:
            caixa, prejuizo = _rebalancear(
                posicoes, caixa, prejuizo, escolher(dia), custos, resultado
            )
            resultado.carteiras[dia] = sorted(posicoes)

        patrimonio.append(caixa + sum(p.valor for p in posicoes.values()))
        referencia.append(cdi_acumulado)

    resultado.patrimonio = pd.Series(patrimonio, index=pregoes)
    resultado.cdi = pd.Series(referencia, index=pregoes)
    return resultado


def _rebalancear(
    posicoes: dict[str, Posicao],
    caixa: float,
    prejuizo: float,
    escolhidos: list[str],
    custos: Custos,
    resultado: Resultado,
) -> tuple[float, float]:
    total = caixa + sum(p.valor for p in posicoes.values())
    alvo = {papel: total / len(escolhidos) for papel in escolhidos} if escolhidos else {}

    ganho, negociado = 0.0, 0.0
    for papel in list(posicoes):
        posicao = posicoes[papel]
        venda = posicao.valor - alvo.get(papel, 0.0)
        if venda <= 0:
            continue
        fracao = venda / posicao.valor
        custo_da_venda = venda * custos.por_lado
        ganho += venda - posicao.custo * fracao - custo_da_venda
        posicao.custo *= 1 - fracao
        posicao.valor -= venda
        caixa += venda - custo_da_venda
        negociado += venda
        resultado.custos_pagos += custo_da_venda
        if posicao.valor <= 1e-9:
            del posicoes[papel]

    base_do_imposto = ganho - prejuizo
    if base_do_imposto > 0:
        imposto = base_do_imposto * custos.imposto
        caixa -= imposto
        resultado.imposto_pago += imposto
        prejuizo = 0.0
    else:
        prejuizo = -base_do_imposto

    compras = {
        papel: valor - (posicoes[papel].valor if papel in posicoes else 0.0)
        for papel, valor in alvo.items()
    }
    compras = {papel: valor for papel, valor in compras.items() if valor > 0}
    necessario = sum(compras.values()) * (1 + custos.por_lado)
    escala = min(1.0, caixa / necessario) if necessario > 0 else 0.0
    for papel, valor in compras.items():
        compra = valor * escala
        custo_da_compra = compra * custos.por_lado
        posicao = posicoes.setdefault(papel, Posicao(0.0, 0.0))
        posicao.valor += compra
        posicao.custo += compra + custo_da_compra
        caixa -= compra + custo_da_compra
        negociado += compra
        resultado.custos_pagos += custo_da_compra

    resultado.giro.append(negociado / total if total > 0 else 0.0)
    return caixa, prejuizo
