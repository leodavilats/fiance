"""A ponte entre o livro-razão e a posição corrente.

O portão G1 sai quando toda posição corrente é derivável do razão e um teste
compara as duas em cada build. Este módulo é os dois lados dessa frase: escreve
o razão em paralelo à posição (`mirror_*`), e sabe dizer onde os dois divergem
(`reconcile`).

A ordem importa e é a do plano: razão em paralelo, comparação lado a lado, e só
então a posição vira projeção. Trocar a fonte antes de a comparação estar verde
é como se perde a confiança no número.
"""

from __future__ import annotations

import logging

from app.core.brt import now_brt
from app.ledger import LedgerEntry, TransactionKind, explain_position, project_positions
from app.ledger.projection import PositionProjection
from app.storage import audit_store, ledger_store, portfolio_store

logger = logging.getLogger("fiance.ledger")

#: Tolerância da comparação. Quantidade fracionária de desdobramento e custo em
#: float acumulam resíduo; a troca por Decimal é um refactor à parte,
#: deliberadamente separado deste.
QUANTITY_TOLERANCE = 1e-6
PRICE_TOLERANCE = 1e-4


def today_brt() -> str:
    return now_brt().strftime("%Y-%m-%d")


# --------------------------------------------------------------------------
# Escrita espelhada
# --------------------------------------------------------------------------


def mirror_position_state(
    ticker: str,
    quantity: float,
    avg_price: float,
    traded_on: str | None = None,
    user_id: str | None = None,
) -> None:
    """Registra no razão o estado que o usuário declarou na tela.

    É `adjust`, não `buy`: a pessoa disse "eu tenho 100 a 10,00", e inventar uma
    compra que não aconteceu seria mentir sobre a origem do número. Quando a
    importação de nota e CSV chegar (G2), ela grava `buy` de verdade e este
    caminho vira exceção em vez de regra.
    """
    try:
        ledger_store.record(
            LedgerEntry(
                kind=TransactionKind.ADJUST,
                symbol=ticker,
                traded_on=traded_on or today_brt(),
                quantity=quantity,
                price=avg_price,
            ),
            source="position_editor",
            user_id=user_id,
        )
    except Exception:
        # Espelhar não pode derrubar a escrita de carteira: a posição corrente
        # ainda é a fonte de leitura. A divergência aparece na reconciliação.
        logger.warning("Falha ao espelhar posição %s no razão", ticker, exc_info=True)


def mirror_sale(
    ticker: str,
    quantity: float,
    price: float,
    fees: float = 0.0,
    traded_on: str | None = None,
    user_id: str | None = None,
) -> None:
    """Venda é operação de verdade, então entra no razão como `sell`."""
    try:
        ledger_store.record(
            LedgerEntry(
                kind=TransactionKind.SELL,
                symbol=ticker,
                traded_on=traded_on or today_brt(),
                quantity=quantity,
                price=price,
                fees=max(0.0, fees),
            ),
            source="sell",
            user_id=user_id,
        )
    except Exception:
        logger.warning("Falha ao espelhar venda de %s no razão", ticker, exc_info=True)


def mirror_removal(ticker: str, user_id: str | None = None) -> None:
    """Apagar a posição zera o razão daquele ativo, senão a projeção ressuscita."""
    try:
        ledger_store.record(
            LedgerEntry(
                kind=TransactionKind.ADJUST,
                symbol=ticker,
                traded_on=today_brt(),
                quantity=0.0,
                price=0.0,
            ),
            source="position_editor",
            user_id=user_id,
        )
    except Exception:
        logger.warning("Falha ao espelhar remoção de %s no razão", ticker, exc_info=True)


# --------------------------------------------------------------------------
# Projeção e reconciliação
# --------------------------------------------------------------------------


def project(user_id: str | None = None) -> dict[str, PositionProjection]:
    return project_positions(ledger_store.list_entries(user_id=user_id))


def reconcile(user_id: str | None = None) -> dict:
    """Compara a posição corrente com a projeção do razão, ativo por ativo.

    Devolve as divergências com os dois números à vista. É o critério de saída
    do G1 escrito como verificação, não como intenção.
    """
    stored = {item["ticker"]: item for item in portfolio_store.list_positions(user_id)}
    projected = {symbol: state for symbol, state in project(user_id).items() if state.is_open}

    differences: list[dict] = []

    for ticker in sorted(set(stored) | set(projected)):
        current = stored.get(ticker)
        derived = projected.get(ticker)

        if current is None:
            differences.append(
                {
                    "ticker": ticker,
                    "reason": "no_razao_sem_posicao",
                    "stored": None,
                    "projected": derived.as_dict(),
                }
            )
            continue

        if derived is None:
            differences.append(
                {
                    "ticker": ticker,
                    "reason": "posicao_sem_razao",
                    "stored": current,
                    "projected": None,
                }
            )
            continue

        quantity_off = abs(current["quantity"] - derived.quantity) > QUANTITY_TOLERANCE
        price_off = abs(current["avg_price"] - derived.avg_price) > PRICE_TOLERANCE

        if quantity_off or price_off:
            differences.append(
                {
                    "ticker": ticker,
                    "reason": "quantidade" if quantity_off else "preco_medio",
                    "stored": current,
                    "projected": derived.as_dict(),
                }
            )

    return {
        "positions": len(stored),
        "projected": len(projected),
        "differences": differences,
        "in_sync": not differences,
    }


def backfill_from_positions(user_id: str | None = None) -> int:
    """Semeia o razão com o estado atual de quem já tinha carteira.

    Sem isto, a reconciliação acusaria toda conta anterior ao razão como
    divergente — e um alarme que toca para todo mundo é um alarme desligado.
    Grava um `adjust` por posição, na data de hoje, com a origem declarada.
    """
    existing = set(ledger_store.symbols(user_id=user_id))
    entries = [
        LedgerEntry(
            kind=TransactionKind.ADJUST,
            symbol=item["ticker"],
            traded_on=today_brt(),
            quantity=item["quantity"],
            price=item["avg_price"],
            note="Estado importado da carteira anterior ao livro-razão.",
        )
        for item in portfolio_store.list_positions(user_id)
        if item["ticker"] not in existing
    ]

    if not entries:
        return 0

    ledger_store.record_many(entries, source="backfill", user_id=user_id)
    audit_store.write(
        audit_store.LEDGER_WRITE,
        entity="ledger",
        summary=f"{len(entries)} posição(ões) semeadas no livro-razão.",
        detail={"symbols": [e.symbol for e in entries]},
        user_id=user_id,
    )
    return len(entries)


def derivation_for(symbol: str, user_id: str | None = None) -> dict:
    """A conta do preço médio de um ativo, passo a passo."""
    entries = ledger_store.list_entries(symbol=symbol, user_id=user_id)
    return explain_position(entries, symbol=symbol.strip().upper())
