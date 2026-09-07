from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.core.errors import DomainError
from app.core.money import ZERO, money, quantize, to_float

TIPOS_DE_DIVIDA = (
    "rotativo_cartao",
    "cheque_especial",
    "credito_pessoal",
    "financiamento_imovel",
    "financiamento_veiculo",
    "parcelamento",
    "outros",
)


class DebtError(DomainError):
    pass


class ClasseDaDivida(StrEnum):
    CARA = "expensive"
    ADMINISTRAVEL = "manageable"
    SEM_TAXA = "no_rate"


@dataclass(frozen=True)
class Debt:
    """Uma dívida declarada. `monthly_rate` em % ao mês; `None` é **não informada**."""

    kind: str
    description: str
    balance: float
    monthly_rate: float | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if self.kind not in TIPOS_DE_DIVIDA:
            raise DebtError(
                f"Tipo de dívida {self.kind!r} não existe. "
                f"O vocabulário é fechado: {', '.join(TIPOS_DE_DIVIDA)}."
            )

        if not self.description or not self.description.strip():
            raise DebtError("Dívida sem descrição.")

        if self.balance <= 0:
            raise DebtError("Dívida com saldo zero ou negativo não é dívida.")

        if self.monthly_rate is not None and self.monthly_rate < 0:
            raise DebtError("Taxa negativa não é dívida — é rendimento.")


@dataclass(frozen=True)
class DividaClassificada:
    """A dívida com a leitura. `taxa_de_virada` é a taxa em que o veredito muda."""

    divida: Debt
    classe: ClasseDaDivida
    referencia_mensal: Decimal | None
    fonte_da_referencia: str
    taxa_de_virada: Decimal | None

    @property
    def cara(self) -> bool:
        return self.classe is ClasseDaDivida.CARA

    def as_dict(self) -> dict:
        return {
            "id": self.divida.id,
            "kind": self.divida.kind,
            "description": self.divida.description,
            "balance": self.divida.balance,
            "monthly_rate": self.divida.monthly_rate,
            "class": self.classe.value,
            "reference_monthly": (
                None
                if self.referencia_mensal is None
                else to_float(quantize(self.referencia_mensal, Decimal("0.0001")))
            ),
            "reference_source": self.fonte_da_referencia,
            "flip_rate": (
                None
                if self.taxa_de_virada is None
                else to_float(quantize(self.taxa_de_virada, Decimal("0.0001")))
            ),
        }


def classificar(
    divida: Debt,
    retorno_mensal_da_carteira: float | None,
    cdi_mensal: float | None = None,
) -> DividaClassificada:
    """Classifica por **custo**, nunca por tipo."""
    if divida.monthly_rate is None:
        return DividaClassificada(
            divida=divida,
            classe=ClasseDaDivida.SEM_TAXA,
            referencia_mensal=None,
            fonte_da_referencia="sem_taxa_informada",
            taxa_de_virada=None,
        )

    if retorno_mensal_da_carteira is not None:
        referencia = money(retorno_mensal_da_carteira)
        fonte = "carteira"
    elif cdi_mensal is not None:
        referencia = money(cdi_mensal)
        fonte = "cdi"
    else:
        return DividaClassificada(
            divida=divida,
            classe=ClasseDaDivida.SEM_TAXA,
            referencia_mensal=None,
            fonte_da_referencia="sem_referencia",
            taxa_de_virada=None,
        )

    taxa = money(divida.monthly_rate)
    classe = ClasseDaDivida.CARA if taxa > referencia else ClasseDaDivida.ADMINISTRAVEL

    return DividaClassificada(
        divida=divida,
        classe=classe,
        referencia_mensal=referencia,
        fonte_da_referencia=fonte,
        taxa_de_virada=referencia,
    )


def classificar_todas(
    dividas: Iterable[Debt],
    retorno_mensal_da_carteira: float | None,
    cdi_mensal: float | None = None,
) -> tuple[DividaClassificada, ...]:
    """As caras primeiro, e entre elas a de maior taxa — que é a que custa mais esperar."""
    lidas = [classificar(d, retorno_mensal_da_carteira, cdi_mensal) for d in dividas]

    def ordem(d: DividaClassificada) -> tuple:
        prioridade = {
            ClasseDaDivida.CARA: 0,
            ClasseDaDivida.SEM_TAXA: 1,
            ClasseDaDivida.ADMINISTRAVEL: 2,
        }[d.classe]
        taxa = -(d.divida.monthly_rate or 0.0)
        return (prioridade, taxa, d.divida.description)

    return tuple(sorted(lidas, key=ordem))


def saldo_caro(lidas: Iterable[DividaClassificada]) -> Decimal:
    total = ZERO
    for d in lidas:
        if d.cara:
            total += money(d.divida.balance)
    return total
