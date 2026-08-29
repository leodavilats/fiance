from __future__ import annotations

from dataclasses import dataclass

OPTIMISTIC_FACTOR = 1.5

DISCLAIMER = (
    "Projeção não é previsão. A faixa mostra três contas com premissas "
    "diferentes, não a probabilidade de cada uma acontecer."
)


@dataclass(frozen=True)
class Scenario:
    code: str
    label: str
    portfolio_factor: float
    dividend_factor: float
    rationale: str

    def rates(self, portfolio_growth_yearly: float, dividend_growth_yearly: float) -> tuple:
        return (
            portfolio_growth_yearly * self.portfolio_factor,
            dividend_growth_yearly * self.dividend_factor,
        )


CONSERVATIVE = Scenario(
    code="conservador",
    label="Conservador",
    portfolio_factor=0.0,
    dividend_factor=0.0,
    rationale=(
        "A carteira não valoriza e os dividendos não crescem. Só o aporte trabalha. "
        "É o único cenário que não depende de previsão."
    ),
)

BASE = Scenario(
    code="base",
    label="Base",
    portfolio_factor=1.0,
    dividend_factor=1.0,
    rationale="As premissas que você informou, aplicadas mês a mês.",
)

OPTIMISTIC = Scenario(
    code="otimista",
    label="Otimista",
    portfolio_factor=OPTIMISTIC_FACTOR,
    dividend_factor=OPTIMISTIC_FACTOR,
    rationale=(
        f"As mesmas premissas multiplicadas por {OPTIMISTIC_FACTOR:.1f}. "
        "Este número não é uma estimativa: é a largura escolhida para a faixa."
    ),
)

SCENARIOS: tuple[Scenario, ...] = (CONSERVATIVE, BASE, OPTIMISTIC)


def band(values: list[float]) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    return (min(values), max(values))
