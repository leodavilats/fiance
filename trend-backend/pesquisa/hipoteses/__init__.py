from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd

from pesquisa.dados import Base

Escolher = Callable[[Base, pd.Timestamp, dict], list[str]]


@dataclass(frozen=True)
class Hipotese:
    nome: str
    descricao: str
    escolher: Escolher
    parametros: dict = field(default_factory=dict)
    congelada: bool = False


def todas() -> dict[str, Hipotese]:
    from pesquisa.hipoteses import momento

    return {h.nome: h for h in (momento.MOMENTO_12_1,)}
