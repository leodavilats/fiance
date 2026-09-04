from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from app.core.config import get_settings


class Affirmation(IntEnum):
    DESCRIPTIVE = 1
    ANALYTICAL = 2
    PRESCRIPTIVE = 3


DISCLAIMERS: dict[Affirmation, str] = {
    Affirmation.DESCRIPTIVE: (
        "Este painel descreve a situação da sua carteira. Não avalia ativos individualmente "
        "nem sugere operações."
    ),
    Affirmation.ANALYTICAL: (
        "Leitura de critérios objetivos gerada por sistema automatizado, com a metodologia "
        "à vista em cada número. Não é recomendação de compra ou venda e não considera a sua "
        "situação financeira, seus objetivos nem a sua tolerância a risco."
    ),
    Affirmation.PRESCRIPTIVE: (
        "As sugestões abaixo são geradas automaticamente a partir das metas que você "
        "declarou. Não são recomendação personalizada de investimento e não substituem "
        "análise ou consultoria de profissional habilitado."
    ),
}

ACTION_FIELDS = frozenset(
    {
        "amount",
        "allocated_cash",
        "suggested_amount",
        "suggested_investment",
        "suggested_quantity",
        "invest_amount",
        "quantity",
        "shares",
        "action",
        "action_label",
        "recommended_action",
        "suggested_action",
    }
)

ASSET_LEVEL_FIELDS = frozenset(
    {"allocations", "suggestions", "top_buys", "top_sells", "opportunities", "items"}
)


@dataclass(frozen=True)
class Mode:
    level: Affirmation
    disclaimer: str
    prescriptive: bool
    asset_level: bool
    personalized: bool

    def as_dict(self) -> dict:
        return {
            "level": int(self.level),
            "name": self.level.name.lower(),
            "disclaimer": self.disclaimer,
            "prescriptive": self.prescriptive,
            "asset_level": self.asset_level,
            "personalized": self.personalized,
        }


def current() -> Mode:
    settings = get_settings()

    try:
        nivel = Affirmation(int(settings.affirmation_level))
    except (ValueError, TypeError):
        nivel = Affirmation.ANALYTICAL

    prescritivo = nivel is Affirmation.PRESCRIPTIVE

    return Mode(
        level=nivel,
        disclaimer=DISCLAIMERS[nivel],
        prescriptive=prescritivo,
        asset_level=nivel >= Affirmation.ANALYTICAL,
        personalized=not prescritivo or settings.suitability_personalization_allowed,
    )


def apply(payload: dict, mode: Mode | None = None) -> dict:
    modo = mode or current()

    resultado = _walk(payload, modo)
    resultado["affirmation"] = modo.as_dict()
    return resultado


def _walk(value, modo: Mode):
    if isinstance(value, dict):
        saida = {}
        for chave, item in value.items():
            if not modo.asset_level and chave in ASSET_LEVEL_FIELDS:
                saida[chave] = []
                continue
            if not modo.prescriptive and chave in ACTION_FIELDS:
                saida[chave] = None
                continue
            saida[chave] = _walk(item, modo)
        return saida

    if isinstance(value, list):
        return [_walk(item, modo) for item in value]

    return value
