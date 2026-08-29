from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, getcontext, localcontext

MONEY_SCALE = Decimal("0.01")

MONEY_ROUNDING = ROUND_HALF_UP

QUANTITY_SCALE = Decimal("0.00000001")

WORKING_PRECISION = 38

getcontext().prec = max(getcontext().prec, WORKING_PRECISION)

ZERO = Decimal("0")


def money(value: object) -> Decimal:
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
    return money(value).quantize(scale, rounding=MONEY_ROUNDING)


def to_float(value: object) -> float:
    return float(money(value))


def cents(value: object) -> int:
    return int(quantize(value) * 100)


def from_cents(value: int) -> Decimal:
    return money(value) / Decimal(100)


def exact() -> localcontext:
    ctx = localcontext()
    ctx.prec = WORKING_PRECISION
    return ctx


def sum_money(values) -> Decimal:
    total = ZERO
    for value in values:
        total += money(value)
    return total
