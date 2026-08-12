from pydantic import BaseModel, Field

from .dashboard import CategoryAllocation
from .quick_invest import QuickInvestAllocation


class RebalanceResponse(BaseModel):
    needs_rebalance: bool
    allocations: list[CategoryAllocation]
    total_gap_amount: float = Field(
        0.0, description="Soma do que falta investir nas categorias abaixo da meta (R$)"
    )
    suggestions: list[QuickInvestAllocation] = Field(default_factory=list)
    message: str
