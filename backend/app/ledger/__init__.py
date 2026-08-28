"""Livro-razão: os lançamentos e a projeção de posição que sai deles.

O módulo é puro — não conhece banco, sessão nem usuário. Recebe uma lista de
lançamentos ordenada e devolve a posição resultante. É assim que dá para testar
uma carteira sintética de cinco anos contra valores calculados à mão.
"""

from .entries import (
    LEDGER_KINDS,
    LedgerEntry,
    LedgerError,
    TransactionKind,
)
from .projection import (
    PositionProjection,
    explain_position,
    project_position,
    project_positions,
)

__all__ = [
    "LEDGER_KINDS",
    "LedgerEntry",
    "LedgerError",
    "PositionProjection",
    "explain_position",
    "TransactionKind",
    "project_position",
    "project_positions",
]
