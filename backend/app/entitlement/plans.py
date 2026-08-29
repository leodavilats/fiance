from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Plan(StrEnum):
    FREE = "free"
    PREMIUM = "premium"


PLAN_ORDER: tuple[Plan, ...] = (Plan.FREE, Plan.PREMIUM)


class Feature(StrEnum):
    PORTFOLIO = "portfolio"
    PORTFOLIO_SUMMARY = "portfolio_summary"
    TODAY_STATUS = "today_status"
    DIVIDENDS_RECEIVED = "dividends_received"
    ACCOUNT_EXPORT = "account_export"

    TODAY_NEXT_ACTION = "today_next_action"
    STRATEGY = "strategy"
    QUICK_INVEST = "quick_invest"
    RF_VS_STOCKS = "rf_vs_stocks"
    PROJECTION = "projection"

    PERFORMANCE_HISTORY = "performance_history"
    DIVIDENDS_PROJECTED = "dividends_projected"
    TAX_REPORT = "tax_report"
    LEDGER_IMPORT = "ledger_import"

    ASSET_PAGE = "asset_page"
    OPPORTUNITY_FILTERS = "opportunity_filters"
    DIP_DIAGNOSIS = "dip_diagnosis"
    COMPARE = "compare"
    GOALS = "goals"
    PRICE_ALERTS = "price_alerts"


@dataclass(frozen=True)
class Rule:
    feature: Feature
    min_plan: Plan
    free_limit: int | None = None
    premium_limit: int | None = None
    unit: str = "usos"
    rationale: str = ""
    monthly: bool = True


RULES: dict[Feature, Rule] = {
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
    rule = RULES[feature]
    return PLAN_ORDER.index(plan) >= PLAN_ORDER.index(rule.min_plan)


def as_dicts() -> list[dict]:
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
