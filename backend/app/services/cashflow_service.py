from __future__ import annotations

import logging
from decimal import Decimal

from app.cashflow import (
    Cascata,
    CashEntry,
    CashKind,
    MonthProjection,
    classificar_todas,
    gasto_fixo_mensal,
    montar,
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


def sincronizar_proventos(user_id: str | None = None) -> int:
    """Refaz as entradas de provento a partir do razão.

    Provento creditado é lançamento do razão, e o razão já é a fonte da carteira. O caixa **lê**
    esse dado em vez de receber um lançamento próprio — se as duas coisas coexistissem, o mesmo
    dinheiro contaria duas vezes e inflaria a renda do mês e a sobra junto.

    É reconstrução, não sincronização incremental: apagar e refazer é a única forma de a segunda
    leitura não divergir da primeira em silêncio. Mesmo padrão de `rebuild_projection`.
    """
    recebidos = portfolio_store.list_dividends_received(user_id=user_id)

    derivadas = [
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
        for row in recebidos
        if row["amount"] > 0
    ]

    return cash_store.replace_derived(derivadas, user_id=user_id)


def mes(
    referencia: str | None = None, user_id: str | None = None, sincronizar: bool = True
) -> MonthProjection:
    if sincronizar:
        sincronizar_proventos(user_id=user_id)

    return projetar_mes(
        cash_store.list_entries(user_id=user_id),
        referencia or mes_corrente(),
    )


def registrar(entry: CashEntry, user_id: str | None = None) -> int:
    """A porta única de escrita do caixa.

    `CashEntry` já recusa provento sem `derived`, valor negativo e categoria fora do vocabulário
    — a validação mora no tipo, e não aqui. O que esta função acrescenta é a fronteira: nenhuma
    rota escreve em `cash_store` direto, do mesmo jeito que nenhuma escreve em `ledger_store`.
    """
    return cash_store.add_entry(entry, user_id=user_id)


def marcar_paga(entry_id: int, paid_on: str | None = None, user_id: str | None = None) -> None:
    cash_store.mark_paid(entry_id, paid_on or hoje(), user_id=user_id)


def apagar(entry_id: int, user_id: str | None = None) -> None:
    cash_store.delete_entry(entry_id, user_id=user_id)


def _mensal_de_anual(taxa_anual_pct: float) -> float:
    """Anual para mensal, por juros compostos — nunca dividindo por doze.

    Dividir por doze **superestima** a referência (12% ao ano dão 0,9489% ao mês compostos, e
    1,0% na conta ingênua), e uma referência inflada **afrouxa** o julgamento: dívida a 0,97% ao
    mês é mais cara que o CDI real e sairia como administrável. O erro cairia do lado de não
    avisar, que é o pior dos dois lados aqui.
    """
    return ((1.0 + taxa_anual_pct / 100.0) ** (1.0 / 12.0) - 1.0) * 100.0


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
    """A ponte: o mês projetado e a ordem do que fazer com o piso da sobra.

    `referencia_mensal` é o que **a carteira da pessoa** rende ao mês. Sem carteira, o CDI que o
    BCB já entrega entra no lugar — nunca um número de mercado solto.
    """
    projecao = mes(referencia=mes_referencia, user_id=user_id)
    entradas = cash_store.list_entries(user_id=user_id)

    cdi_mensal = None if cdi_anual is None else _mensal_de_anual(cdi_anual)

    lidas = classificar_todas(
        cash_store.list_debts(user_id=user_id),
        retorno_mensal_da_carteira=referencia_mensal if tem_carteira else None,
        cdi_mensal=cdi_mensal,
    )

    cascata = montar(
        projecao.sobra_piso,
        lidas,
        reserva_meses_alvo=reserva_meses_alvo,
        reserva_atual=reserva_atual if reserva_atual is not None else ZERO,
        gasto_fixo=gasto_fixo_mensal(entradas),
        desvio_de_meta=desvio_de_meta,
    )

    return projecao, cascata


def dividas(
    *,
    referencia_mensal: float | None,
    tem_carteira: bool,
    cdi_anual: float | None = None,
    user_id: str | None = None,
) -> list[dict]:
    cdi_mensal = None if cdi_anual is None else _mensal_de_anual(cdi_anual)
    lidas = classificar_todas(
        cash_store.list_debts(user_id=user_id),
        retorno_mensal_da_carteira=referencia_mensal if tem_carteira else None,
        cdi_mensal=cdi_mensal,
    )
    return [d.as_dict() for d in lidas]


def gasto_fixo(user_id: str | None = None) -> Decimal:
    return gasto_fixo_mensal(cash_store.list_entries(user_id=user_id))


def tem_caixa(user_id: str | None = None) -> bool:
    """Se existe caixa lançado — a pergunta que deriva a porta de entrada.

    Entrada derivada do razão **não** conta: quem só tem provento sincronizado não lançou caixa
    nenhum, e mandá-lo para o `Mês` seria a tela vazia que a IA nova declarou como risco.
    """
    return any(not e.derived for e in cash_store.list_entries(user_id=user_id))
