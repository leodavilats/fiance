from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.errors import DomainError
from app.core.pagination import MAX_PAGE_SIZE, clamp_limit, paginate
from app.entitlement import Feature, requires
from app.importing import parse_import
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
async def list_transactions(
    symbol: str | None = None,
    limit: int | None = Query(None, ge=1, le=MAX_PAGE_SIZE),
    cursor: str | None = Query(None, description="Cursor devolvido em `next_cursor`."),
) -> dict:
    """Lançamentos em ordem de leitura, do mais recente para o mais antigo.

    Aqui a paginação corta no banco de verdade: não há agregado sobre a lista,
    então limitar a consulta não distorce número nenhum.
    """
    page_size = clamp_limit(limit)
    rows = ledger_store.list_entries(symbol=symbol, limit=page_size, cursor=cursor, descending=True)
    page = paginate(rows, page_size, key=lambda e: e.traded_on, identity=lambda e: e.id)
    entries = page.items

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
        "next_cursor": page.next_cursor,
        "has_more": page.has_more,
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


class ImportPreviewRequest(BaseModel):
    content: str = Field(description="Texto colado ou conteúdo do arquivo CSV.")
    format: str | None = Field(
        default=None, description="'csv' ou 'list'. Omitido, é detectado pelo cabeçalho."
    )


class ImportCommitRequest(BaseModel):
    content: str
    format: str | None = None
    include_duplicates: bool = Field(
        default=False,
        description=(
            "Quando falso, linhas idênticas a lançamentos já existentes ficam de fora. "
            "A escolha é do usuário porque duas compras iguais no mesmo dia acontecem."
        ),
    )


@router.post("/transactions/import/preview")
async def preview_import(body: ImportPreviewRequest) -> dict:
    """Lê sem gravar: mostra o que entrou, o que falhou e o que é repetido.

    A prévia devolve as linhas boas **e** os problemas ao mesmo tempo, de
    propósito: parar no primeiro erro faria o usuário corrigir um arquivo de
    trezentas linhas uma linha por vez.
    """
    parsed = parse_import(
        body.content, default_day=ledger_service.today_brt(), force_format=body.format
    )
    ledger_service.mark_duplicates(parsed)
    return parsed.as_dict()


class ImportRejected(DomainError):
    status_code = 422


@router.post(
    "/transactions/import",
    dependencies=[Depends(requires(Feature.LEDGER_IMPORT))],
)
async def commit_import(body: ImportCommitRequest) -> dict:
    """Grava a importação. Tudo ou nada.

    Validar linha a linha e gravar o que passou deixaria a carteira num estado
    que o usuário não pediu e não consegue desfazer — e num produto que calcula
    IR, meia importação é pior que nenhuma.
    """
    parsed = parse_import(
        body.content, default_day=ledger_service.today_brt(), force_format=body.format
    )

    if parsed.issues:
        raise ImportRejected(
            f"{len(parsed.issues)} linha(s) com problema. Corrija antes de importar: "
            + "; ".join(f"linha {i.line}: {i.message}" for i in parsed.issues[:3])
        )

    ledger_service.mark_duplicates(parsed)
    selecionadas = [
        row.entry for row in parsed.rows if body.include_duplicates or row.duplicate_of is None
    ]
    ignoradas = len(parsed.rows) - len(selecionadas)

    ids = ledger_service.import_entries(selecionadas)
    return {"imported": len(ids), "skipped_duplicates": ignoradas, "ids": ids}
