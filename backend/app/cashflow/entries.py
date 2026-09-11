from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from app.core.errors import DomainError


class CashError(DomainError):
    pass


class CashKind(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"


CASH_KINDS = frozenset(kind.value for kind in CashKind)


CATEGORIAS_DE_DESPESA = (
    "moradia",
    "contas_da_casa",
    "mercado",
    "transporte",
    "saude",
    "educacao",
    "lazer",
    "cuidados_pessoais",
    "divida",
    "outros",
)

CATEGORIAS_DE_ENTRADA = (
    "salario",
    "decimo_terceiro",
    "ferias",
    "renda_variavel",
    "provento",
    "reembolso",
    "outros",
)

CATEGORIAS_FIXAS = frozenset({"moradia", "contas_da_casa", "educacao"})

CATEGORIAS_VARIAVEIS = frozenset(
    {"mercado", "transporte", "saude", "lazer", "cuidados_pessoais", "outros"}
)

CATEGORIAS_QUE_NAO_SAO_CONSUMO = frozenset({"divida"})

CATEGORIAS_FORA_DA_BASE_DE_RENDA = frozenset({"provento", "reembolso"})


@dataclass(frozen=True)
class CashEntry:
    kind: CashKind
    category: str
    description: str
    amount: float
    due_on: str
    paid_on: str | None = None
    id: int | None = None
    recurrence_id: int | None = None
    derived: bool = False
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise CashError("Lançamento de caixa sem descrição.")

        _conferir_data(self.due_on, "vencimento")
        if self.paid_on is not None:
            _conferir_data(self.paid_on, "pagamento")

        if self.amount <= 0:
            raise CashError(
                "Valor negativo não é lançamento — é sinal trocado. "
                "Entrada e saída se distinguem por `kind`, não pelo sinal do valor."
            )

        validas = CATEGORIAS_DE_ENTRADA if self.kind is CashKind.INCOME else CATEGORIAS_DE_DESPESA
        if self.category not in validas:
            raise CashError(
                f"Categoria {self.category!r} não existe para {self.kind}. "
                f"O vocabulário é fechado: {', '.join(validas)}."
            )

        if self.category == "provento" and not self.derived:
            raise CashError(
                "Provento não se lança no caixa: ele é derivado do razão, que já é a fonte da "
                "carteira. Lançar aqui contaria o mesmo dinheiro duas vezes."
            )

        if self.derived and self.category != "provento":
            raise CashError(f"Lançamento derivado só existe para provento; veio {self.category!r}.")

    @property
    def mes(self) -> str:
        return self.competencia[:7]

    @property
    def competencia(self) -> str:
        return self.paid_on or self.due_on

    @property
    def realizado(self) -> bool:
        return self.paid_on is not None

    @property
    def comprometido(self) -> bool:
        return self.paid_on is None

    @property
    def eh_consumo(self) -> bool:
        return self.kind is CashKind.EXPENSE and self.category not in CATEGORIAS_QUE_NAO_SAO_CONSUMO

    @property
    def sort_key(self) -> tuple:
        return (self.competencia, self.id if self.id is not None else 0)


def _conferir_data(valor: str, papel: str) -> None:
    if len(valor) != 10 or valor[4] != "-" or valor[7] != "-":
        raise CashError(f"Data de {papel} deve ser YYYY-MM-DD no fuso brasileiro; veio {valor!r}.")
