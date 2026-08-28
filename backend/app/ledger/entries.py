"""Os tipos de lançamento e a validação de cada um.

A lista é fechada. Lançamento cujo tipo o projetor não conhece não pode existir
no banco: seria um buraco silencioso na posição corrente, que é justamente o
que o livro-razão veio impedir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from app.core.errors import DomainError


class LedgerError(DomainError):
    """Lançamento que não pode existir."""


class TransactionKind(StrEnum):
    BUY = "buy"
    SELL = "sell"

    #: Desdobramento e grupamento. Multiplicam a quantidade por `ratio_to /
    #: ratio_from` e deixam o custo total intacto — logo o preço médio se ajusta
    #: sozinho. Desdobramento sem ajuste é preço médio errado, que é IR errado.
    SPLIT = "split"

    #: Bonificação em ações: quantidade nova com custo declarado (em geral o
    #: valor patrimonial informado pela companhia, às vezes zero).
    BONUS = "bonus"

    #: Transferência entre corretoras: muda de lugar, não muda custo nem
    #: quantidade da carteira. Existe para o extrato bater com a nota.
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"

    #: Amortização de FII e de renda fixa: devolve capital, reduz o custo sem
    #: reduzir a quantidade.
    AMORTIZATION = "amortization"

    #: Estado declarado pelo usuário na tela de posição. Não é uma operação: é
    #: a pessoa dizendo "eu tenho 100 a 10,00". O projetor o trata como reset,
    #: e é o que mantém a posição corrente derivável do razão enquanto a
    #: importação de nota e CSV não existe.
    ADJUST = "adjust"


LEDGER_KINDS = frozenset(kind.value for kind in TransactionKind)

#: Tipos em que preço é obrigatório e precisa ser positivo.
_PRICED = frozenset({TransactionKind.BUY, TransactionKind.SELL})

#: Tipos que movimentam quantidade e por isso exigem quantidade positiva.
#: `ADJUST` fica de fora: zero é um estado declarável — é como o usuário diz
#: "não tenho mais este ativo", e é o que a remoção de posição registra.
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
    """Um lançamento. `traded_on` é dia no fuso brasileiro, `YYYY-MM-DD`."""

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
        """Ordem canônica: dia, depois id.

        O id desempata dentro do mesmo dia porque é a ordem em que os
        lançamentos entraram — e vender antes de comprar no mesmo dia dá
        quantidade negativa por um instante, o que muda o preço médio.
        """
        return (self.traded_on, self.id if self.id is not None else 0)
