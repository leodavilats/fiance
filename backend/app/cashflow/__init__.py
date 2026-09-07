"""O caixa: matemática pura, sem banco. Módulo irmão de `ledger/`."""

from .cascata import Cascata, Passo, TipoDePasso, gasto_fixo_mensal, montar
from .debt import (
    TIPOS_DE_DIVIDA,
    ClasseDaDivida,
    Debt,
    DebtError,
    DividaClassificada,
    classificar,
    classificar_todas,
    saldo_caro,
)
from .entries import (
    CASH_KINDS,
    CATEGORIAS_DE_DESPESA,
    CATEGORIAS_DE_ENTRADA,
    CATEGORIAS_FIXAS,
    CATEGORIAS_FORA_DA_BASE_DE_RENDA,
    CATEGORIAS_QUE_NAO_SAO_CONSUMO,
    CATEGORIAS_VARIAVEIS,
    CashEntry,
    CashError,
    CashKind,
)
from .month import Estimativa, MonthProjection, estimar_variavel, projetar_mes

__all__ = [
    "CASH_KINDS",
    "CATEGORIAS_DE_DESPESA",
    "CATEGORIAS_DE_ENTRADA",
    "CATEGORIAS_FIXAS",
    "CATEGORIAS_FORA_DA_BASE_DE_RENDA",
    "CATEGORIAS_QUE_NAO_SAO_CONSUMO",
    "CATEGORIAS_VARIAVEIS",
    "TIPOS_DE_DIVIDA",
    "Cascata",
    "CashEntry",
    "CashError",
    "CashKind",
    "ClasseDaDivida",
    "Debt",
    "DebtError",
    "DividaClassificada",
    "Estimativa",
    "MonthProjection",
    "Passo",
    "TipoDePasso",
    "classificar",
    "classificar_todas",
    "estimar_variavel",
    "gasto_fixo_mensal",
    "montar",
    "projetar_mes",
    "saldo_caro",
]
