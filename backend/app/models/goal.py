from pydantic import BaseModel, Field


class Goal(BaseModel):
    category: str = Field(
        ...,
        description="'renda_fixa' | 'acoes_br' | 'acoes_int' | 'fiis' | 'cripto'",
    )
    target_pct: float = Field(..., ge=0, le=100)
    target_value: float | None = Field(None, ge=0, description="Meta em R$ (opcional)")
    deadline: str | None = Field(None, description="Prazo no formato YYYY-MM-DD (opcional)")


class SectorGoal(BaseModel):
    sector: str = Field(..., description="Nome do setor (ex: 'Financeiro', 'Energia')")
    target_pct: float = Field(..., ge=0, le=100, description="% dentro do total de ações")


class GoalsRequest(BaseModel):
    goals: list[Goal]


class SectorGoalsRequest(BaseModel):
    sector_goals: list[SectorGoal]
