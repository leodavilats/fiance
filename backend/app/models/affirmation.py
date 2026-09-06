from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator


class AffirmationMode(BaseModel):
    level: int = Field(description="1 descritivo · 2 analítico · 3 prescritivo.")
    name: str
    disclaimer: str
    prescriptive: bool = Field(
        description="Verdadeiro quando o produto pode dizer quanto aportar em qual ativo."
    )
    asset_level: bool = Field(description="Verdadeiro quando o produto avalia ativo individual.")
    personalized: bool


_EMAIL = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")


class InterestSignupRequest(BaseModel):
    email: str = Field(max_length=254)
    source: str = Field(default="landing", max_length=40)

    @field_validator("email")
    @classmethod
    def _formato(cls, valor: str) -> str:
        limpo = valor.strip().lower()
        if not _EMAIL.match(limpo):
            raise ValueError("E-mail invalido.")
        return limpo


class InterestSignupResponse(BaseModel):
    registered: bool = Field(
        description="Falso quando o e-mail ja estava na lista. Nao e erro: cadastrar duas vezes "
        "e o comportamento normal de quem nao lembra se ja cadastrou."
    )
