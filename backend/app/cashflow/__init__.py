"""O caixa: matemática pura, sem banco.

Módulo irmão de `ledger/`, e com a mesma disciplina — o que mora aqui não sabe que existe banco
de dados. `cashflow_service` é quem liga isto à API e às tabelas, do mesmo jeito que
`apuracao_service` liga `ledger/apuracao.py`.

A fronteira que importa: **este módulo não conhece o razão**. Provento creditado é entrada de
caixa e lançamento do razão ao mesmo tempo, e a regra de não contar duas vezes vive no tipo
(`CashEntry` recusa provento que não venha marcado como derivado). Quem faz a leitura derivada é
a camada de serviço, porque é ela que tem os dois lados.
"""

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
