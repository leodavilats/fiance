from typing import List
from pydantic import BaseModel, Field


class Goal(BaseModel):
    category: str = Field(..., description="'renda' | 'trade' | 'cripto' | 'caixa'")
    target_pct: float = Field(..., ge=0, le=100)


class GoalsRequest(BaseModel):
    goals: List[Goal]
