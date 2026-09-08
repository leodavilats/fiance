"""O mês anterior como molde do próximo: o que repete, e só o que repete."""

from __future__ import annotations

from calendar import monthrange
from collections.abc import Iterable
from dataclasses import dataclass

from .entries import (
    CATEGORIAS_FIXAS,
    CATEGORIAS_QUE_NAO_SAO_CONSUMO,
    CashEntry,
    CashError,
    CashKind,
)

# Décimo terceiro e férias acontecem uma vez no ano; provento vem do razão; reembolso é evento.
# O que sobra de recorrente por natureza é o salário.
CATEGORIAS_DE_ENTRADA_QUE_REPETEM = frozenset({"salario"})

CATEGORIAS_DE_DESPESA_QUE_REPETEM = CATEGORIAS_FIXAS | CATEGORIAS_QUE_NAO_SAO_CONSUMO


@dataclass(frozen=True)
class Candidato:
    """Um lançamento do mês de origem, já datado no destino."""

    entry: CashEntry
    repete: bool
    ja_esta_la: bool

    def as_dict(self) -> dict:
        return {
            "kind": self.entry.kind.value,
            "category": self.entry.category,
            "description": self.entry.description,
            "amount": self.entry.amount,
            "due_on": self.entry.due_on,
            "repeats": self.repete,
            "already_there": self.ja_esta_la,
        }


def repete_todo_mes(entry: CashEntry) -> bool:
    """Se o lançamento é do tipo que volta no mês seguinte por natureza, não por hábito."""
    if entry.derived:
        return False
    if entry.kind is CashKind.INCOME:
        return entry.category in CATEGORIAS_DE_ENTRADA_QUE_REPETEM
    return entry.category in CATEGORIAS_DE_DESPESA_QUE_REPETEM


def _identidade(entry: CashEntry) -> tuple[str, str, str]:
    """O que faz dois lançamentos serem o mesmo. O valor fica de fora: a conta de luz muda."""
    return (entry.kind.value, entry.category, entry.description.strip().casefold())


def dia_no_mes(data: str, mes: str) -> str:
    """Mesmo dia, outro mês — preso ao último dia quando o mês de destino é mais curto."""
    ano, m = int(mes[:4]), int(mes[5:7])
    dia = min(int(data[8:10]), monthrange(ano, m)[1])
    return f"{mes}-{dia:02d}"


def _conferir_mes(valor: str, papel: str) -> None:
    if len(valor) != 7 or valor[4] != "-" or not valor[:4].isdigit() or not valor[5:].isdigit():
        raise CashError(f"Mês de {papel} deve ser YYYY-MM; veio {valor!r}.")


def montar_molde(entries: Iterable[CashEntry], de_mes: str, para_mes: str) -> tuple[Candidato, ...]:
    """Os candidatos a copiar de um mês para o outro, em ordem de dia."""
    _conferir_mes(de_mes, "origem")
    _conferir_mes(para_mes, "destino")

    if de_mes == para_mes:
        raise CashError("Um mês não é molde de si mesmo.")

    todos = list(entries)
    origem = [e for e in todos if e.mes == de_mes and not e.derived]
    destino = {_identidade(e) for e in todos if e.mes == para_mes}

    candidatos = [
        Candidato(
            entry=CashEntry(
                kind=e.kind,
                category=e.category,
                description=e.description,
                amount=e.amount,
                due_on=dia_no_mes(e.due_on, para_mes),
                paid_on=None,
            ),
            repete=repete_todo_mes(e),
            ja_esta_la=_identidade(e) in destino,
        )
        for e in origem
    ]

    return tuple(sorted(candidatos, key=lambda c: (c.entry.due_on, c.entry.description)))
