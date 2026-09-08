from __future__ import annotations

import logging
from decimal import Decimal

from app.cashflow import (
    Candidato,
    Cascata,
    CashEntry,
    CashError,
    CashKind,
    Debt,
    DividaClassificada,
    MonthProjection,
    classificar_todas,
    gasto_fixo_mensal,
    montar,
    montar_molde,
    projetar_mes,
)
from app.core.brt import now_brt
from app.core.money import ZERO
from app.storage import cash_store, portfolio_store

logger = logging.getLogger("fiance.cashflow")


def mes_corrente() -> str:
    agora = now_brt()
    return f"{agora.year:04d}-{agora.month:02d}"


def hoje() -> str:
    return now_brt().strftime("%Y-%m-%d")


def _proventos_derivados(user_id: str | None = None) -> list[CashEntry]:
    """As entradas de provento, derivadas do razão **em memória**."""
    return [
        CashEntry(
            kind=CashKind.INCOME,
            category="provento",
            description=f"Provento de {row['ticker']}",
            amount=row["amount"],
            due_on=row["paid_at"],
            paid_on=row["paid_at"],
            derived=True,
            metadata={"derived_from": f"dividend:{row['id']}"},
        )
        for row in portfolio_store.list_dividends_received(user_id=user_id)
        if row["amount"] > 0
    ]


def entradas(user_id: str | None = None) -> list[CashEntry]:
    """O caixa completo: o que foi lançado, mais o que é derivado do razão."""
    return cash_store.list_entries(user_id=user_id) + _proventos_derivados(user_id=user_id)


def mes(referencia: str | None = None, user_id: str | None = None) -> MonthProjection:
    return projetar_mes(entradas(user_id=user_id), referencia or mes_corrente())


def registrar(entry: CashEntry, user_id: str | None = None) -> int:
    """A porta única de escrita do caixa."""
    if entry.derived:
        raise CashError(
            "Entrada derivada do razão não se grava: ela é projeção, montada na leitura."
        )
    return cash_store.add_entry(entry, user_id=user_id)


def registrar_varias(entries: list[CashEntry], user_id: str | None = None) -> list[int]:
    """O lote passa pela mesma porta, e a mesma recusa vale para cada um."""
    for entry in entries:
        if entry.derived:
            raise CashError(
                "Entrada derivada do razão não se grava: ela é projeção, montada na leitura."
            )
    return cash_store.add_entries(entries, user_id=user_id)


def editar(entry_id: int, entry: CashEntry, user_id: str | None = None) -> CashEntry:
    if entry.derived:
        raise CashError(
            "Provento vem do razão, e é lá que ele se corrige. Editar aqui criaria uma segunda "
            "verdade sobre o mesmo dinheiro."
        )
    return cash_store.update_entry(entry_id, entry, user_id=user_id)


def molde(de_mes: str, para_mes: str, user_id: str | None = None) -> tuple[Candidato, ...]:
    """O mês de origem lido como molde do destino."""
    return montar_molde(entradas(user_id=user_id), de_mes, para_mes)


def mes_anterior(mes: str) -> str:
    ano, m = int(mes[:4]), int(mes[5:7])
    return f"{ano - 1:04d}-12" if m == 1 else f"{ano:04d}-{m - 1:02d}"


def marcar_paga(entry_id: int, paid_on: str | None = None, user_id: str | None = None) -> None:
    cash_store.mark_paid(entry_id, paid_on or hoje(), user_id=user_id)


def apagar(entry_id: int, user_id: str | None = None) -> None:
    cash_store.delete_entry(entry_id, user_id=user_id)


def cadastrar_divida(debt: Debt, user_id: str | None = None) -> int:
    return cash_store.add_debt(debt, user_id=user_id)


def quitar_divida(debt_id: int, user_id: str | None = None) -> None:
    cash_store.settle_debt(debt_id, user_id=user_id)


def _mensal_de_anual(taxa_anual_pct: float) -> float:
    """Anual para mensal, por juros compostos — nunca dividindo por doze."""
    return ((1.0 + taxa_anual_pct / 100.0) ** (1.0 / 12.0) - 1.0) * 100.0


def dividas_lidas(
    *,
    referencia_mensal: float | None,
    tem_carteira: bool,
    cdi_anual: float | None = None,
    user_id: str | None = None,
) -> tuple[DividaClassificada, ...]:
    cdi_mensal = None if cdi_anual is None else _mensal_de_anual(cdi_anual)
    return classificar_todas(
        cash_store.list_debts(user_id=user_id),
        retorno_mensal_da_carteira=referencia_mensal if tem_carteira else None,
        cdi_mensal=cdi_mensal,
    )


def dividas(
    *,
    referencia_mensal: float | None,
    tem_carteira: bool,
    cdi_anual: float | None = None,
    user_id: str | None = None,
) -> list[dict]:
    return [
        d.as_dict()
        for d in dividas_lidas(
            referencia_mensal=referencia_mensal,
            tem_carteira=tem_carteira,
            cdi_anual=cdi_anual,
            user_id=user_id,
        )
    ]


def sobra(
    *,
    referencia_mensal: float | None,
    tem_carteira: bool,
    cdi_anual: float | None = None,
    reserva_meses_alvo: int | None = None,
    reserva_atual: Decimal | None = None,
    desvio_de_meta: str | None = None,
    mes_referencia: str | None = None,
    user_id: str | None = None,
) -> tuple[MonthProjection, Cascata]:
    """A ponte: o mês projetado e a ordem do que fazer com o piso da sobra."""
    todas = entradas(user_id=user_id)
    projecao = projetar_mes(todas, mes_referencia or mes_corrente())

    lidas = dividas_lidas(
        referencia_mensal=referencia_mensal,
        tem_carteira=tem_carteira,
        cdi_anual=cdi_anual,
        user_id=user_id,
    )

    cascata = montar(
        projecao.sobra_piso,
        lidas,
        reserva_meses_alvo=reserva_meses_alvo,
        reserva_atual=reserva_atual if reserva_atual is not None else ZERO,
        gasto_fixo=gasto_fixo_mensal(todas),
        desvio_de_meta=desvio_de_meta,
    )

    return projecao, cascata


def gasto_fixo(user_id: str | None = None) -> Decimal:
    return gasto_fixo_mensal(entradas(user_id=user_id))


def tem_caixa(user_id: str | None = None) -> bool:
    """Se existe caixa lançado — a pergunta que deriva a porta de entrada."""
    return bool(cash_store.list_entries(user_id=user_id))
