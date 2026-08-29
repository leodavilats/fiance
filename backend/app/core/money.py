from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, getcontext, localcontext

from sqlalchemy import BigInteger, Numeric
from sqlalchemy.types import TypeDecorator

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


STORAGE_SCALE = 8

_STORAGE_QUANTUM = Decimal(1).scaleb(-STORAGE_SCALE)

_STORAGE_FACTOR = Decimal(10) ** STORAGE_SCALE


class ExactNumeric(TypeDecorator):
    impl = Numeric

    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(BigInteger())
        return dialect.type_descriptor(Numeric(precision=28, scale=STORAGE_SCALE))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        exato = money(value).quantize(_STORAGE_QUANTUM, rounding=MONEY_ROUNDING)
        if dialect.name == "sqlite":
            return int(exato * _STORAGE_FACTOR)
        return exato

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "sqlite":
            return Decimal(value) / _STORAGE_FACTOR
        return money(value)


Money = ExactNumeric

Quantity = ExactNumeric
