from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.ledger import LedgerEntry, TransactionKind
from app.services import ledger_service
from app.services.ledger_service import derivation_for
from app.storage import audit_store, ledger_store

router = APIRouter()


class TransactionIn(BaseModel):
    kind: TransactionKind
    symbol: str
    traded_on: str = Field(description="Dia da operação no fuso brasileiro, YYYY-MM-DD.")
    quantity: float = 0.0
    price: float = 0.0
    fees: float = 0.0
    ratio_from: float = 1.0
    ratio_to: float = 1.0
    amount: float = 0.0
    note: str | None = None

    def to_entry(self) -> LedgerEntry:
        return LedgerEntry(
            kind=self.kind,
            symbol=self.symbol,
            traded_on=self.traded_on,
            quantity=self.quantity,
            price=self.price,
            fees=self.fees,
            ratio_from=self.ratio_from,
            ratio_to=self.ratio_to,
            amount=self.amount,
            note=self.note,
        )


class TransactionBatch(BaseModel):
    transactions: list[TransactionIn] = Field(default_factory=list)


@router.get("/transactions")
async def list_transactions(symbol: str | None = None, limit: int = 500) -> dict:
    entries = ledger_store.list_entries(symbol=symbol, limit=max(1, min(limit, 2000)))
    return {
        "items": [
            {
                "id": e.id,
                "kind": e.kind.value,
                "symbol": e.symbol,
                "traded_on": e.traded_on,
                "quantity": e.quantity,
                "price": e.price,
                "fees": e.fees,
                "ratio_from": e.ratio_from,
                "ratio_to": e.ratio_to,
                "amount": e.amount,
                "note": e.note,
            }
            for e in entries
        ],
        "count": len(entries),
    }


@router.post("/transactions")
async def create_transaction(body: TransactionIn) -> dict:
    entry = body.to_entry()
    entry_id = ledger_store.record(entry, source="manual")
    audit_store.write(
        audit_store.LEDGER_WRITE,
        entity="transaction",
        entity_id=entry_id,
        summary=f"{entry.kind.value} {entry.symbol} em {entry.traded_on}.",
        detail={"quantity": entry.quantity, "price": entry.price, "fees": entry.fees},
    )
    return {"id": entry_id}


@router.post("/transactions/batch")
async def create_transactions(body: TransactionBatch) -> dict:
    """Importação é atômica: um lançamento inválido recusa o lote inteiro.

    Validar item a item e gravar o que passou deixaria a carteira num estado
    que o usuário não pediu e não consegue desfazer.
    """
    entries = [item.to_entry() for item in body.transactions]
    ids = ledger_store.record_many(entries, source="import")
    audit_store.write(
        audit_store.LEDGER_WRITE,
        entity="transaction",
        summary=f"{len(ids)} lançamento(s) importados.",
    )
    return {"ids": ids, "count": len(ids)}


@router.delete("/transactions/{entry_id}")
async def delete_transaction(entry_id: int) -> dict:
    ledger_store.delete_entry(entry_id)
    audit_store.write(
        audit_store.LEDGER_DELETE,
        entity="transaction",
        entity_id=entry_id,
        summary=f"Lançamento {entry_id} removido.",
    )
    return {"deleted": entry_id}


@router.get("/transactions/derivation/{symbol}")
async def read_derivation(symbol: str) -> dict:
    """A conta que produziu o preço médio, passo a passo.

    Critério de aceite do G1: a tela expõe, em texto, como o número apareceu.
    Preço médio que ninguém consegue conferir é preço médio em que ninguém
    confia — e é o número que vai para a declaração.
    """
    return derivation_for(symbol)


@router.get("/transactions/reconciliation")
async def read_reconciliation() -> dict:
    """Onde a posição corrente e a projeção do razão discordam."""
    return ledger_service.reconcile()


@router.post("/transactions/backfill")
async def backfill(user_id: str = Depends(get_current_user)) -> dict:
    """Semeia o razão com a carteira atual, para contas anteriores a ele."""
    seeded = ledger_service.backfill_from_positions(user_id=user_id)
    return {"seeded": seeded}


@router.get("/activity")
async def read_activity(action: str | None = None, limit: int = 100) -> dict:
    """O log append-only, do ponto de vista do titular."""
    return {"items": audit_store.read(action=action, limit=limit)}
