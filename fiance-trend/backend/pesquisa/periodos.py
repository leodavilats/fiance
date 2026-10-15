from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Periodo:
    nome: str
    inicio: date
    fim: date | None

    def contem(self, dia: date) -> bool:
        return self.inicio <= dia and (self.fim is None or dia <= self.fim)


ESTUDO = Periodo("estudo", date(2005, 1, 1), date(2018, 12, 31))
VALIDACAO = Periodo("validacao", date(2019, 1, 1), date(2022, 12, 31))
PROVA = Periodo("prova", date(2023, 1, 1), None)

PERIODOS = {p.nome: p for p in (ESTUDO, VALIDACAO, PROVA)}
