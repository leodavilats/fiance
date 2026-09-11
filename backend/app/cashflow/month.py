from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from app.core.money import ZERO, money, quantize, sum_money, to_float

from .entries import (
    CATEGORIAS_FORA_DA_BASE_DE_RENDA,
    CATEGORIAS_VARIAVEIS,
    CashEntry,
    CashKind,
)

MESES_DE_BASE = 3


@dataclass(frozen=True)
class Estimativa:
    meses_de_base: tuple[str, ...]
    esperado_baixo: Decimal
    esperado_alto: Decimal
    ja_gasto: Decimal
    restante_baixo: Decimal
    restante_alto: Decimal

    @property
    def existe(self) -> bool:
        return bool(self.meses_de_base)

    def as_dict(self) -> dict:
        return {
            "base_months": list(self.meses_de_base),
            "expected_low": to_float(quantize(self.esperado_baixo)),
            "expected_high": to_float(quantize(self.esperado_alto)),
            "spent_so_far": to_float(quantize(self.ja_gasto)),
            "remaining_low": to_float(quantize(self.restante_baixo)),
            "remaining_high": to_float(quantize(self.restante_alto)),
        }


@dataclass(frozen=True)
class MonthProjection:
    mes: str
    entrou: Decimal
    saiu: Decimal
    comprometido: Decimal
    livre_agora: Decimal
    estimativa: Estimativa
    sobra_piso: Decimal
    sobra_teto: Decimal
    a_vencer: tuple[CashEntry, ...]
    renda_de_base: Decimal

    @property
    def tem_faixa(self) -> bool:
        return self.estimativa.existe

    @property
    def negativa(self) -> bool:
        return self.sobra_piso < ZERO

    def as_dict(self) -> dict:
        return {
            "month": self.mes,
            "received": to_float(quantize(self.entrou)),
            "paid": to_float(quantize(self.saiu)),
            "committed": to_float(quantize(self.comprometido)),
            "free_now": to_float(quantize(self.livre_agora)),
            "surplus_low": to_float(quantize(self.sobra_piso)),
            "surplus_high": to_float(quantize(self.sobra_teto)),
            "has_range": self.tem_faixa,
            "income_baseline": to_float(quantize(self.renda_de_base)),
            "estimate": self.estimativa.as_dict(),
            "due": [
                {
                    "id": e.id,
                    "category": e.category,
                    "description": e.description,
                    "amount": e.amount,
                    "due_on": e.due_on,
                }
                for e in self.a_vencer
            ],
        }


def _do_mes(entries: Iterable[CashEntry], mes: str) -> list[CashEntry]:
    return [e for e in entries if e.mes == mes]


def _variavel_por_mes(entries: Iterable[CashEntry]) -> dict[str, Decimal]:
    totais: dict[str, Decimal] = {}
    for e in entries:
        if e.kind is not CashKind.EXPENSE or e.category not in CATEGORIAS_VARIAVEIS:
            continue
        if not e.realizado:
            continue
        totais[e.mes] = totais.get(e.mes, ZERO) + money(e.amount)
    return totais


def estimar_variavel(
    entries: Iterable[CashEntry], mes: str, meses_de_base: int = MESES_DE_BASE
) -> Estimativa:
    todos = list(entries)
    por_mes = _variavel_por_mes(todos)

    fechados = sorted(m for m in por_mes if m < mes)[-meses_de_base:]
    ja_gasto = por_mes.get(mes, ZERO)

    if not fechados:
        return Estimativa(
            meses_de_base=(),
            esperado_baixo=ZERO,
            esperado_alto=ZERO,
            ja_gasto=ja_gasto,
            restante_baixo=ZERO,
            restante_alto=ZERO,
        )

    valores = [por_mes[m] for m in fechados]
    baixo, alto = min(valores), max(valores)

    return Estimativa(
        meses_de_base=tuple(fechados),
        esperado_baixo=baixo,
        esperado_alto=alto,
        ja_gasto=ja_gasto,
        restante_baixo=max(ZERO, baixo - ja_gasto),
        restante_alto=max(ZERO, alto - ja_gasto),
    )


def projetar_mes(
    entries: Iterable[CashEntry], mes: str, meses_de_base: int = MESES_DE_BASE
) -> MonthProjection:
    todos = sorted(entries, key=lambda e: e.sort_key)
    do_mes = _do_mes(todos, mes)

    entrou = sum_money(money(e.amount) for e in do_mes if e.kind is CashKind.INCOME and e.realizado)
    saiu = sum_money(money(e.amount) for e in do_mes if e.kind is CashKind.EXPENSE and e.realizado)

    a_vencer = tuple(e for e in do_mes if e.kind is CashKind.EXPENSE and e.comprometido)
    comprometido = sum_money(money(e.amount) for e in a_vencer)

    livre_agora = entrou - saiu - comprometido

    estimativa = estimar_variavel(todos, mes, meses_de_base)
    sobra_piso = livre_agora - estimativa.restante_alto
    sobra_teto = livre_agora - estimativa.restante_baixo

    renda_de_base = sum_money(
        money(e.amount)
        for e in do_mes
        if e.kind is CashKind.INCOME
        and e.realizado
        and e.category not in CATEGORIAS_FORA_DA_BASE_DE_RENDA
    )

    return MonthProjection(
        mes=mes,
        entrou=entrou,
        saiu=saiu,
        comprometido=comprometido,
        livre_agora=livre_agora,
        estimativa=estimativa,
        sobra_piso=sobra_piso,
        sobra_teto=sobra_teto,
        a_vencer=a_vencer,
        renda_de_base=renda_de_base,
    )
