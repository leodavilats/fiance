from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from app.core.errors import DomainError


class LedgerError(DomainError):
    pass


class TransactionKind(StrEnum):
    BUY = "buy"
    SELL = "sell"

    SPLIT = "split"

    BONUS = "bonus"

    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"

    AMORTIZATION = "amortization"

    ADJUST = "adjust"


LEDGER_KINDS = frozenset(kind.value for kind in TransactionKind)

_PRICED = frozenset({TransactionKind.BUY, TransactionKind.SELL})

_QUANTITY_BEARING = frozenset(
    {
        TransactionKind.BUY,
        TransactionKind.SELL,
        TransactionKind.BONUS,
        TransactionKind.TRANSFER_IN,
        TransactionKind.TRANSFER_OUT,
    }
)


@dataclass(frozen=True)
class LedgerEntry:
    kind: TransactionKind
    symbol: str
    traded_on: str
    quantity: float = 0.0
    price: float = 0.0
    fees: float = 0.0
    ratio_from: float = 1.0
    ratio_to: float = 1.0
    amount: float = 0.0
    id: int | None = None
    instrument_id: int | None = None
    note: str | None = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.symbol or not self.symbol.strip():
            raise LedgerError("Lançamento sem ativo.")

        if len(self.traded_on) != 10 or self.traded_on[4] != "-" or self.traded_on[7] != "-":
            raise LedgerError(
                f"Data do lançamento deve ser YYYY-MM-DD no fuso brasileiro; veio {self.traded_on!r}."
            )

        if self.kind in _QUANTITY_BEARING and self.quantity <= 0:
            raise LedgerError(f"Lançamento {self.kind} exige quantidade positiva.")

        if self.quantity < 0:
            raise LedgerError("Quantidade negativa não é lançamento — é sinal trocado.")

        if self.kind in _PRICED and self.price <= 0:
            raise LedgerError(f"Lançamento {self.kind} exige preço positivo.")

        if self.fees < 0:
            raise LedgerError("Custo de operação não pode ser negativo.")

        if self.kind is TransactionKind.SPLIT:
            if self.ratio_from <= 0 or self.ratio_to <= 0:
                raise LedgerError("Proporção de desdobramento precisa de dois lados positivos.")
            if self.ratio_from == self.ratio_to:
                raise LedgerError("Desdobramento 1:1 não muda nada — não é lançamento.")

        if self.kind is TransactionKind.AMORTIZATION and self.amount <= 0:
            raise LedgerError("Amortização exige valor devolvido positivo.")

    @property
    def sort_key(self) -> tuple:
        return (self.traded_on, self.id if self.id is not None else 0)
