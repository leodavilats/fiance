from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from pesquisa.ranking import sinais

Calcular = Callable[[pd.DataFrame, pd.DataFrame, int, dict], pd.Series]


@dataclass(frozen=True)
class Sinal:
    nome: str
    descricao: str
    calcular: Calcular
    parametros: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Classe:
    nome: str
    volume_minimo: float
    desde: date


SINAIS = {
    s.nome: s
    for s in (
        Sinal(
            "momento_risco",
            "Retorno de 12 meses sem o último, dividido pela volatilidade anualizada",
            sinais.momento_risco,
            {"janela": 252, "pulo": 21},
        ),
        Sinal(
            "distancia_mm200",
            "Distância do preço à média de 200 pregões, em desvios-padrão",
            sinais.distancia_media,
            {"janela": 200},
        ),
        Sinal(
            "inclinacao_r2",
            "Inclinação anual da reta do log do preço em 126 pregões, vezes o R²",
            sinais.inclinacao_r2,
            {"janela": 126},
        ),
    )
}

CLASSES = {c.nome: c for c in (Classe("acoes", 5_000_000, date(2005, 1, 1)),)}
