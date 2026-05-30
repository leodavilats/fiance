from pydantic import BaseModel, Field


class Goal(BaseModel):
    category: str = Field(
        ...,
        description="'renda_fixa' | 'acoes_br' | 'acoes_int' | 'fiis' | 'cripto'",
    )
    target_pct: float = Field(..., ge=0, le=100)
    target_value: float | None = Field(None, ge=0, description="Meta em R$ (opcional)")
    deadline: str | None = Field(None, description="Prazo no formato YYYY-MM-DD (opcional)")


class GoalsRequest(BaseModel):
    goals: list[Goal]
