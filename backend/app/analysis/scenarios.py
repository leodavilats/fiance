"""Cenários de projeção — a faixa, não o número.

Uma projeção de renda passiva a cinco anos é uma multiplicação de três chutes:
quanto a carteira valoriza, quanto os dividendos crescem, e quanto a pessoa
consegue aportar todo mês. Apresentar o resultado como ``R$ 3.847,21`` empresta
a essa pilha de chutes uma precisão de centavo que ela não tem — e a pessoa
decide quanto poupar em cima disso.

Por isso a faixa não é um enfeite opcional ao lado do número: ela viaja
**dentro** do mesmo objeto que o número. Não existe caminho no payload em que
alguém consiga renderizar o valor projetado sem ter o piso e o teto na mão.

Os três cenários não são um intervalo de confiança. Não há distribuição aqui, e
fingir que há seria o mesmo erro com mais casas decimais. São três contas
declaradas:

* **Conservador** — a carteira não valoriza e os dividendos não crescem. Só o
  aporte trabalha. É o único dos três que não depende de previsão nenhuma, e é
  o que a pessoa precisa conseguir suportar.
* **Base** — as premissas que a própria pessoa informou.
* **Otimista** — as mesmas premissas com metade a mais. Não é previsão: é a
  largura escolhida para a faixa, e está escrita como tal na resposta.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Quanto o cenário otimista estica as premissas informadas. Um número
#: escolhido, não estimado — e a resposta diz isso ao cliente para que a tela
#: possa dizer ao usuário.
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

#: A ordem importa: é a ordem em que a faixa é lida (piso, meio, teto).
SCENARIOS: tuple[Scenario, ...] = (CONSERVATIVE, BASE, OPTIMISTIC)


def band(values: list[float]) -> tuple[float, float]:
    """Piso e teto de um mesmo mês entre os cenários.

    Recebe os valores já calculados em vez de recalcular porque quem chama já
    os tem — e porque uma segunda implementação da mesma conta é uma segunda
    chance de elas discordarem.
    """
    if not values:
        return (0.0, 0.0)
    return (min(values), max(values))
