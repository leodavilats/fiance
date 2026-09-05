from __future__ import annotations

from pydantic import BaseModel, Field


class AffirmationMode(BaseModel):
    level: int = Field(description="1 descritivo · 2 analítico · 3 prescritivo.")
    name: str
    disclaimer: str
    prescriptive: bool = Field(
        description="Verdadeiro quando o produto pode dizer quanto aportar em qual ativo."
    )
    asset_level: bool = Field(description="Verdadeiro quando o produto avalia ativo individual.")
    personalized: bool
