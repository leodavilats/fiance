"""Dicionário de eventos de produto — fechado, e fechado de propósito.

Cada evento existe porque responde uma das seis perguntas do funil. Evento sem
pergunta associada é dívida de dado: custa privacidade e não produz decisão.

Duas regras que a implementação garante, não recomenda:

* **Nome fora do dicionário é rejeitado.** Não há evento livre.
* **Nenhum valor monetário, ticker ou posição entra.** As propriedades passam
  por uma lista de chaves permitidas e por um teto de tamanho; o que sobra é
  categórico. Quando a magnitude importa, vai como faixa anônima.
"""

from __future__ import annotations

from dataclasses import dataclass

QUESTION_ENTRY = "A pessoa entra?"
QUESTION_PORTFOLIO = "Cadastra carteira?"
QUESTION_VALUE = "Chega ao momento de valor?"
QUESTION_RETURN = "Volta?"
QUESTION_LIMIT = "Encosta no limite?"
QUESTION_PAY = "Paga?"

QUESTIONS = (
    QUESTION_ENTRY,
    QUESTION_PORTFOLIO,
    QUESTION_VALUE,
    QUESTION_RETURN,
    QUESTION_LIMIT,
    QUESTION_PAY,
)


@dataclass(frozen=True)
class EventSpec:
    name: str
    question: str
    description: str


_SPECS: tuple[EventSpec, ...] = (
    # A pessoa entra?
    EventSpec("signup_completed", QUESTION_ENTRY, "Conta criada."),
    EventSpec("onboarding_started", QUESTION_ENTRY, "Primeiro passo do onboarding aberto."),
    EventSpec("onboarding_step_completed", QUESTION_ENTRY, "Um passo concluído (prop: step)."),
    EventSpec("onboarding_abandoned", QUESTION_ENTRY, "Saída sem concluir (prop: step)."),
    EventSpec("onboarding_completed", QUESTION_ENTRY, "Onboarding concluído."),
    # Cadastra carteira?
    EventSpec("portfolio_import_started", QUESTION_PORTFOLIO, "Importação aberta."),
    EventSpec("portfolio_import_method", QUESTION_PORTFOLIO, "Método escolhido (prop: method)."),
    EventSpec(
        "portfolio_first_position_added",
        QUESTION_PORTFOLIO,
        "Primeira posição salva — é o gatilho do trial.",
    ),
    EventSpec(
        "portfolio_reached_4_assets",
        QUESTION_PORTFOLIO,
        "Carteira legível: quatro ativos, mínimo para o veredito de risco.",
    ),
    # Chega ao momento de valor?
    EventSpec("first_diagnosis_viewed", QUESTION_VALUE, "Primeiro diagnóstico visto."),
    EventSpec("next_action_viewed", QUESTION_VALUE, "N3 de Hoje, a próxima ação."),
    EventSpec("quick_invest_completed", QUESTION_VALUE, "Aporte simulado até o fim."),
    EventSpec("dip_diagnosis_opened", QUESTION_VALUE, "Diagnóstico de queda aberto."),
    EventSpec("health_verdict_viewed", QUESTION_VALUE, "Veredito de saúde da carteira visto."),
    EventSpec("why_this_opened", QUESTION_VALUE, "Painel de explicabilidade aberto."),
    # Volta?
    EventSpec("session_started", QUESTION_RETURN, "Sessão iniciada."),
    EventSpec("push_opened", QUESTION_RETURN, "Notificação aberta."),
    EventSpec("feed_item_opened", QUESTION_RETURN, "Item do feed de Hoje aberto."),
    EventSpec(
        "strategy_visited_on_contribution_day",
        QUESTION_RETURN,
        "Estratégia aberta no dia de aporte.",
    ),
    # Encosta no limite?
    EventSpec("limit_reached", QUESTION_LIMIT, "Teto de plano atingido (props: feature, plan)."),
    EventSpec("paywall_viewed", QUESTION_LIMIT, "Gate exibido (props: origin, feature)."),
    EventSpec("trial_started", QUESTION_LIMIT, "Trial iniciado pela primeira posição."),
    EventSpec("trial_ended", QUESTION_LIMIT, "Trial encerrado (prop: reason)."),
    # Paga?
    EventSpec("upgrade_started", QUESTION_PAY, "Fluxo de assinatura iniciado (prop: origin)."),
    EventSpec("checkout_completed", QUESTION_PAY, "Checkout concluído (prop: plan)."),
    EventSpec("subscription_started", QUESTION_PAY, "Assinatura ativa (props: plan, channel)."),
    EventSpec("subscription_cancelled", QUESTION_PAY, "Cancelamento (prop: reason)."),
    EventSpec("refund_requested", QUESTION_PAY, "Reembolso pedido (prop: reason)."),
    # Indicação: o único canal de aquisição que cabe na aritmética deste
    # produto. As duas etapas são separadas porque a distância entre elas é a
    # medida que importa — atribuir é barato, qualificar é que custa.
    EventSpec("referral_attributed", QUESTION_PAY, "Conta chegou por um código de indicação."),
    EventSpec("referral_qualified", QUESTION_PAY, "Indicação virou crédito (1ª posição salva)."),
)

CATALOG: dict[str, EventSpec] = {spec.name: spec for spec in _SPECS}

# Eventos de *aha*: são estes que a regressão de D30 testa para descobrir qual é
# o momento de valor verdadeiro.
AHA_EVENTS = (
    "first_diagnosis_viewed",
    "next_action_viewed",
    "quick_invest_completed",
    "dip_diagnosis_opened",
)

# Chaves permitidas nas propriedades. Tudo categórico: nada que identifique
# ativo, valor ou posição.
ALLOWED_PROP_KEYS = frozenset(
    {
        "step",
        "method",
        "origin",
        "source",
        "feature",
        "plan",
        "channel",
        "reason",
        "variant",
        "platform",
        "size_bucket",
        "position_index",
    }
)

# Chaves explicitamente proibidas. Existem na lista para que a tentativa falhe
# alto em teste, em vez de ser silenciosamente descartada por não estar na
# lista de permitidas.
FORBIDDEN_PROP_KEYS = frozenset(
    {
        "ticker",
        "symbol",
        "amount",
        "value",
        "price",
        "quantity",
        "patrimony",
        "total",
        "balance",
        "pnl",
        "email",
        "name",
    }
)

MAX_PROP_VALUE_LENGTH = 48
MAX_PROPS = 8

ALLOWED_PLATFORMS = frozenset({"web", "android", "ios", "server"})


class InvalidEventError(ValueError):
    """Evento fora do dicionário, ou propriedade que não pode ser gravada."""


def validate(name: str, props: dict | None, platform: str) -> tuple[str, dict[str, str]]:
    if name not in CATALOG:
        raise InvalidEventError(f"Evento desconhecido: {name!r}.")

    if platform not in ALLOWED_PLATFORMS:
        raise InvalidEventError(f"Plataforma desconhecida: {platform!r}.")

    clean: dict[str, str] = {}
    for key, value in (props or {}).items():
        lowered = str(key).lower()
        if lowered in FORBIDDEN_PROP_KEYS:
            raise InvalidEventError(
                f"Propriedade {key!r} não pode ir para analytics: "
                "dado de carteira não sai do produto."
            )
        if lowered not in ALLOWED_PROP_KEYS:
            raise InvalidEventError(f"Propriedade {key!r} não está no dicionário de eventos.")
        if value is None:
            continue
        if isinstance(value, bool):
            text = "true" if value else "false"
        elif isinstance(value, int | float):
            text = str(value)
        else:
            text = str(value)
        if len(text) > MAX_PROP_VALUE_LENGTH:
            raise InvalidEventError(f"Valor de {key!r} excede {MAX_PROP_VALUE_LENGTH} caracteres.")
        clean[lowered] = text

    if len(clean) > MAX_PROPS:
        raise InvalidEventError(f"No máximo {MAX_PROPS} propriedades por evento.")

    return name, clean


def catalog_as_dicts() -> list[dict]:
    return [
        {"name": spec.name, "question": spec.question, "description": spec.description}
        for spec in _SPECS
    ]
