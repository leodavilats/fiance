from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.core.money import ZERO, money, quantize, to_float

from .debt import DividaClassificada, saldo_caro
from .entries import CATEGORIAS_FIXAS, CashEntry, CashKind


class TipoDePasso(StrEnum):
    DIVIDA = "debt"
    RESERVA = "reserve"
    APORTE = "contribution"


@dataclass(frozen=True)
class Passo:
    ordem: int
    tipo: TipoDePasso
    valor: Decimal
    motivo: str
    falsificador: str | None = None
    referencia: str | None = None

    def as_dict(self) -> dict:
        return {
            "order": self.ordem,
            "type": self.tipo.value,
            "amount": to_float(quantize(self.valor)),
            "reason": self.motivo,
            "falsifier": self.falsificador,
            "reference": self.referencia,
        }


@dataclass(frozen=True)
class Cascata:
    """A ordem. Pode terminar **sem** passo de aporte, e isso é resposta, não falha."""

    sobra_piso: Decimal
    passos: tuple[Passo, ...]
    sobrou_para_aporte: Decimal

    @property
    def tem_aporte(self) -> bool:
        return any(p.tipo is TipoDePasso.APORTE for p in self.passos)

    def as_dict(self) -> dict:
        return {
            "surplus_low": to_float(quantize(self.sobra_piso)),
            "steps": [p.as_dict() for p in self.passos],
            "available_to_invest": to_float(quantize(self.sobrou_para_aporte)),
        }


def gasto_fixo_mensal(entries: Iterable[CashEntry], meses: int = 3) -> Decimal:
    """A média do gasto fixo dos meses fechados. Zero quando não há mês fechado."""
    por_mes: dict[str, Decimal] = {}
    for e in entries:
        if e.kind is not CashKind.EXPENSE or e.category not in CATEGORIAS_FIXAS:
            continue
        if not e.realizado:
            continue
        por_mes[e.mes] = por_mes.get(e.mes, ZERO) + money(e.amount)

    if not por_mes:
        return ZERO

    recentes = sorted(por_mes)[-meses:]
    total = sum((por_mes[m] for m in recentes), ZERO)
    return total / len(recentes)


def montar(
    sobra_piso: Decimal,
    dividas: Iterable[DividaClassificada],
    *,
    reserva_meses_alvo: int | None = None,
    reserva_atual: Decimal | None = None,
    gasto_fixo: Decimal = ZERO,
    desvio_de_meta: str | None = None,
) -> Cascata:
    """Monta a ordem sobre o **piso** da faixa, nunca sobre o meio."""
    passos: list[Passo] = []
    disponivel = sobra_piso

    if disponivel <= ZERO:
        return Cascata(sobra_piso=sobra_piso, passos=(), sobrou_para_aporte=ZERO)

    lidas = list(dividas)
    caro = saldo_caro(lidas)

    if caro > ZERO:
        primeira = next(d for d in lidas if d.cara)
        valor = min(disponivel, caro)
        taxa = primeira.divida.monthly_rate or 0.0
        referencia = primeira.referencia_mensal or ZERO

        passos.append(
            Passo(
                ordem=len(passos) + 1,
                tipo=TipoDePasso.DIVIDA,
                valor=valor,
                motivo=(
                    f"{primeira.divida.description} custa {taxa:.2f}% ao mês. "
                    f"Sua {'carteira' if primeira.fonte_da_referencia == 'carteira' else 'referência de renda fixa'} "
                    f"rendeu {to_float(referencia):.2f}% ao mês. Enquanto essa diferença existir, "
                    "quitar rende mais que aportar."
                ),
                falsificador=(
                    f"Se a taxa da dívida cair abaixo de {to_float(referencia):.2f}% ao mês, "
                    "quitar deixa de ser a prioridade."
                ),
                referencia=primeira.fonte_da_referencia,
            )
        )
        disponivel -= valor

    if disponivel > ZERO and reserva_meses_alvo and gasto_fixo > ZERO and reserva_atual is not None:
        alvo = gasto_fixo * reserva_meses_alvo
        falta = alvo - reserva_atual
        if falta > ZERO:
            valor = min(disponivel, falta)
            passos.append(
                Passo(
                    ordem=len(passos) + 1,
                    tipo=TipoDePasso.RESERVA,
                    valor=valor,
                    motivo=(
                        f"Sua reserva cobre "
                        f"{to_float(reserva_atual / gasto_fixo):.1f} meses do seu gasto fixo, e "
                        f"você declarou {reserva_meses_alvo}. Faltam "
                        f"R$ {to_float(quantize(falta)):.2f}."
                    ),
                    falsificador=(
                        "Se você baixar o alvo de meses, ou se o gasto fixo cair, este passo "
                        "encolhe — a base é o seu custo fixo, não um número de mercado."
                    ),
                    referencia="gasto_fixo_proprio",
                )
            )
            disponivel -= valor

    if disponivel > ZERO:
        passos.append(
            Passo(
                ordem=len(passos) + 1,
                tipo=TipoDePasso.APORTE,
                valor=disponivel,
                motivo=(
                    desvio_de_meta
                    or "Sem meta de alocação declarada, a ordem sai por score — e não por desvio."
                ),
                falsificador=None,
                referencia="meta" if desvio_de_meta else "score",
            )
        )

    return Cascata(
        sobra_piso=sobra_piso,
        passos=tuple(passos),
        sobrou_para_aporte=max(ZERO, disponivel),
    )
