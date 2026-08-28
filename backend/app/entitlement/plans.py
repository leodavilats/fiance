"""A régua de plano, como dado declarativo.

A composição do Premium é a decisão mais provável de ser revista depois dos
primeiros experimentos — e é a mais difícil de reverter depois de publicada. Por
isso ela é uma **tabela**, não uma sequência de condicionais: mudar a régua tem
que ser mudar um valor, não caçar `if premium` por vinte arquivos.

A linha que separa os planos tem uma frase só: **o Free mostra o que aconteceu;
o Premium diz o que fazer a respeito.** Toda dúvida de fronteira se resolve com
ela, e a coluna `rationale` existe para que a decisão possa ser defendida depois
— e reaberta com argumento, não com apetite.

Cercas proibidas, que este módulo não sabe expressar de propósito: número de
ativos na carteira, desfoque de dado do próprio usuário, exportação e exclusão
de conta. Não são "ainda não implementadas": não têm representação aqui porque
não devem existir.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Plan(StrEnum):
    FREE = "free"
    PREMIUM = "premium"


#: Ordem de precedência. Um plano dá acesso a tudo que os anteriores dão.
PLAN_ORDER: tuple[Plan, ...] = (Plan.FREE, Plan.PREMIUM)


class Feature(StrEnum):
    """O que pode ser cercado. Nome estável: vira chave de evento e de gate."""

    # Sempre livre — declarado para que o gate saiba dizer "isto nunca é pago".
    PORTFOLIO = "portfolio"
    PORTFOLIO_SUMMARY = "portfolio_summary"
    TODAY_STATUS = "today_status"
    DIVIDENDS_RECEIVED = "dividends_received"
    ACCOUNT_EXPORT = "account_export"

    # Cercado por nível de intenção: N1/N2 dizem "como estou", N3 diz "o que faço".
    TODAY_NEXT_ACTION = "today_next_action"
    STRATEGY = "strategy"
    QUICK_INVEST = "quick_invest"
    RF_VS_STOCKS = "rf_vs_stocks"
    PROJECTION = "projection"

    # Cercado por profundidade.
    PERFORMANCE_HISTORY = "performance_history"
    DIVIDENDS_PROJECTED = "dividends_projected"
    TAX_REPORT = "tax_report"
    LEDGER_IMPORT = "ledger_import"

    # Cercado por quantidade.
    ASSET_PAGE = "asset_page"
    OPPORTUNITY_FILTERS = "opportunity_filters"
    DIP_DIAGNOSIS = "dip_diagnosis"
    COMPARE = "compare"
    GOALS = "goals"
    PRICE_ALERTS = "price_alerts"


@dataclass(frozen=True)
class Rule:
    """O que cada plano pode fazer com uma feature."""

    feature: Feature
    #: Plano mínimo. `FREE` significa "livre para todo mundo".
    min_plan: Plan
    #: Teto mensal no Free. `None` = sem teto. `0` = bloqueado.
    free_limit: int | None = None
    #: Teto mensal no Premium. `None` = sem teto.
    premium_limit: int | None = None
    #: Unidade do teto, para a mensagem do gate ficar legível.
    unit: str = "usos"
    #: Por que a linha passa aqui. Existe para ser discutida, não decorada.
    rationale: str = ""
    #: Recursos cujo teto reinicia todo mês; os demais são contagem absoluta
    #: (três alertas são três alertas, não três por mês).
    monthly: bool = True


RULES: dict[Feature, Rule] = {
    # ---------------------------------------------------------------- livres
    Feature.PORTFOLIO: Rule(
        Feature.PORTFOLIO,
        Plan.FREE,
        rationale=(
            "Cobrar por registrar o próprio dado pune quem tem mais valor e impede o "
            "veredito de risco, que exige quatro ativos."
        ),
    ),
    Feature.PORTFOLIO_SUMMARY: Rule(
        Feature.PORTFOLIO_SUMMARY,
        Plan.FREE,
        rationale="É o motivo de abrir o app. Trancar mata o hábito e o boca a boca.",
    ),
    Feature.TODAY_STATUS: Rule(
        Feature.TODAY_STATUS,
        Plan.FREE,
        rationale="N1 e N2 são o momento de valor de entrada. Sem eles não há por que voltar.",
    ),
    Feature.DIVIDENDS_RECEIVED: Rule(
        Feature.DIVIDENDS_RECEIVED,
        Plan.FREE,
        rationale="Isca do segmento de renda; a conversão vem depois, nas metas.",
    ),
    Feature.ACCOUNT_EXPORT: Rule(
        Feature.ACCOUNT_EXPORT,
        Plan.FREE,
        rationale=(
            "Portabilidade é direito do titular e exigência de loja. Nunca atrás de plano, "
            "em nenhuma hipótese."
        ),
    ),
    # ------------------------------------------------- cercados por intenção
    Feature.TODAY_NEXT_ACTION: Rule(
        Feature.TODAY_NEXT_ACTION,
        Plan.PREMIUM,
        free_limit=0,
        rationale=(
            "A prévia nomeia o desvio com o número verdadeiro da carteira da pessoa e cobra "
            "pela resposta. É a fronteira entre 'como estou' e 'o que faço'."
        ),
    ),
    Feature.STRATEGY: Rule(
        Feature.STRATEGY,
        Plan.PREMIUM,
        free_limit=0,
        rationale="Núcleo do Premium: é a razão do retorno mensal.",
    ),
    Feature.QUICK_INVEST: Rule(
        Feature.QUICK_INVEST,
        Plan.PREMIUM,
        free_limit=0,
        rationale="É a resposta ao 'o que eu faço com o aporte deste mês'.",
    ),
    Feature.RF_VS_STOCKS: Rule(
        Feature.RF_VS_STOCKS,
        Plan.PREMIUM,
        free_limit=0,
        rationale="Comparação que orienta decisão de alocação, não leitura de estado.",
    ),
    Feature.PROJECTION: Rule(
        Feature.PROJECTION,
        Plan.PREMIUM,
        free_limit=0,
        rationale="Projeção é julgamento sobre o futuro, não histórico.",
    ),
    # ------------------------------------------------ cercados por profundidade
    Feature.PERFORMANCE_HISTORY: Rule(
        Feature.PERFORMANCE_HISTORY,
        Plan.FREE,
        free_limit=12,
        premium_limit=None,
        unit="meses",
        monthly=False,
        rationale=(
            "Limite por profundidade. Quem tem três anos de carteira é exatamente quem paga."
        ),
    ),
    Feature.DIVIDENDS_PROJECTED: Rule(
        Feature.DIVIDENDS_PROJECTED,
        Plan.PREMIUM,
        free_limit=0,
        rationale="Projeção é julgamento, não histórico.",
    ),
    Feature.TAX_REPORT: Rule(
        Feature.TAX_REPORT,
        Plan.PREMIUM,
        free_limit=0,
        rationale=(
            "Alto valor, baixa frequência: é o que segura o cliente em março e justifica o "
            "plano anual. Ver o próprio histórico continua livre; reconstruí-lo é produto."
        ),
    ),
    Feature.LEDGER_IMPORT: Rule(
        Feature.LEDGER_IMPORT,
        Plan.PREMIUM,
        free_limit=0,
        rationale="Ler os próprios lançamentos é direito; importar em massa é trabalho do produto.",
    ),
    # -------------------------------------------------- cercados por quantidade
    Feature.ASSET_PAGE: Rule(
        Feature.ASSET_PAGE,
        Plan.FREE,
        free_limit=5,
        premium_limit=None,
        unit="páginas por mês",
        rationale=(
            "Valor provado antes de cobrado. Ativo da própria carteira **nunca** conta: não "
            "se cobra por olhar o que já é do usuário."
        ),
    ),
    Feature.OPPORTUNITY_FILTERS: Rule(
        Feature.OPPORTUNITY_FILTERS,
        Plan.PREMIUM,
        free_limit=0,
        rationale=(
            "A prévia gera desejo; o filtro é o produto. O custo foi resolvido por "
            "materialização, não por cerca."
        ),
    ),
    Feature.DIP_DIAGNOSIS: Rule(
        Feature.DIP_DIAGNOSIS,
        Plan.FREE,
        free_limit=1,
        premium_limit=None,
        unit="diagnósticos por mês",
        rationale=(
            "Alta urgência: quem chega aqui está com medo. Um grátis converte melhor que zero."
        ),
    ),
    Feature.COMPARE: Rule(
        Feature.COMPARE,
        Plan.FREE,
        free_limit=2,
        premium_limit=4,
        unit="ativos por comparação",
        monthly=False,
        rationale="Degradação suave em vez de bloqueio; barato e demonstra qualidade.",
    ),
    Feature.GOALS: Rule(
        Feature.GOALS,
        Plan.FREE,
        free_limit=1,
        premium_limit=None,
        unit="metas",
        monthly=False,
        rationale="Uma meta cria hábito e gera o desvio; várias são gestão.",
    ),
    Feature.PRICE_ALERTS: Rule(
        Feature.PRICE_ALERTS,
        Plan.FREE,
        free_limit=3,
        premium_limit=None,
        unit="alertas",
        monthly=False,
        rationale="Push custa quase zero e retém muito: três grátis prendem o hábito.",
    ),
}


def rule_for(feature: Feature) -> Rule:
    return RULES[feature]


def limit_for(feature: Feature, plan: Plan) -> int | None:
    rule = RULES[feature]
    return rule.premium_limit if plan is Plan.PREMIUM else rule.free_limit


def allows(feature: Feature, plan: Plan) -> bool:
    """`True` quando o plano alcança a feature, ignorando teto de uso."""
    rule = RULES[feature]
    return PLAN_ORDER.index(plan) >= PLAN_ORDER.index(rule.min_plan)


def as_dicts() -> list[dict]:
    """A régua publicada. A UI monta o texto do gate a partir disto."""
    return [
        {
            "feature": rule.feature.value,
            "min_plan": rule.min_plan.value,
            "free_limit": rule.free_limit,
            "premium_limit": rule.premium_limit,
            "unit": rule.unit,
            "monthly": rule.monthly,
            "rationale": rule.rationale,
        }
        for rule in RULES.values()
    ]
