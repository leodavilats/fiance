"""Dinheiro: escala e arredondamento num lugar só.

Float é adequado para apoiar decisão — a diferença entre R$ 1.203,4499 e
R$ 1.203,45 não muda veredito nenhum. Deixa de ser adequado quando o número é
somado ao longo de centenas de operações e vira o valor que o usuário digita na
declaração: aí o resíduo acumula e o extrato deixa de fechar com a nota.

Duas regras, e elas são o motivo de este módulo existir:

* **Nunca construir `Decimal` a partir de `float` sem passar por texto.**
  `Decimal(0.1)` é `0.1000000000000000055511151231257827…`; `money(0.1)` é
  exatamente `0,10`. Sem essa passagem, trocar float por Decimal só troca o
  lugar onde o erro aparece.
* **Arredondar apenas na borda.** As contas intermediárias rodam em escala
  ampliada; só o valor apresentado ou gravado é quantizado. Arredondar a cada
  passo é como se perde um centavo por operação.

Não é um refactor de todo o código: é o módulo por onde o número fiscal passa.
Preço e patrimônio de tela continuam em float, e continuam certos.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, getcontext, localcontext

#: Centavos. É a escala do Real e a escala em que a Receita quer o número.
MONEY_SCALE = Decimal("0.01")

#: Meio para cima, que é a convenção da apuração brasileira — e não o
#: banker's rounding do `round()` do Python, que arredonda 2,5 para 2.
MONEY_ROUNDING = ROUND_HALF_UP

#: Quantidade de ativo aceita fração (desdobramento, fundos). Escala maior que a
#: do dinheiro porque o resíduo aqui multiplica preço lá na frente.
QUANTITY_SCALE = Decimal("0.00000001")

#: Precisão das contas intermediárias. Larga o bastante para milhares de
#: operações não encostarem no limite.
WORKING_PRECISION = 38

getcontext().prec = max(getcontext().prec, WORKING_PRECISION)

ZERO = Decimal("0")


def money(value: object) -> Decimal:
    """Converte para `Decimal` sem herdar o erro do binário.

    `float` passa por `repr`, que devolve a menor representação decimal que
    volta ao mesmo float — é o que faz `money(0.1)` valer exatamente `0.1`.
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(repr(value))
    if isinstance(value, int):
        return Decimal(value)
    if value is None:
        return ZERO
    return Decimal(str(value))


def quantize(value: object, scale: Decimal = MONEY_SCALE) -> Decimal:
    """Arredonda para a escala declarada. Use só na borda."""
    return money(value).quantize(scale, rounding=MONEY_ROUNDING)


def to_float(value: object) -> float:
    """Volta para float na saída da API. O arredondamento já aconteceu."""
    return float(money(value))


def cents(value: object) -> int:
    """Valor em centavos inteiros — a forma de guardar dinheiro sem escala."""
    return int(quantize(value) * 100)


def from_cents(value: int) -> Decimal:
    return money(value) / Decimal(100)


def exact() -> localcontext:
    """Contexto de precisão ampliada para uma sequência de contas."""
    ctx = localcontext()
    ctx.prec = WORKING_PRECISION
    return ctx


def sum_money(values) -> Decimal:
    """Soma exata. É aqui que mil operações fecham com erro zero."""
    total = ZERO
    for value in values:
        total += money(value)
    return total
