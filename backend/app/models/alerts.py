from pydantic import BaseModel, Field, field_validator

from .portfolio import TICKER_PATTERN

MAX_ALERTS_PER_USER = 100


class AlertCreate(BaseModel):
    ticker: str = Field(..., min_length=4, max_length=32, pattern=TICKER_PATTERN)
    condition: str
    target_price: float
    note: str | None = None

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v: str) -> str:
        if v not in ("above", "below"):
            raise ValueError("condition must be 'above' or 'below'")
        return v

    @field_validator("target_price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("target_price must be positive")
        if v > 1_000_000:
            raise ValueError("target_price implausível para um ativo da B3")
        return v

    @field_validator("note")
    @classmethod
    def validate_note(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 500:
            raise ValueError("note excede 500 caracteres")
        return v
