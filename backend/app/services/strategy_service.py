"""Service para geração de estratégias de investimento."""

from typing import List

from app.analysis.strategy import build_investment_strategy
from app.models import Goal, Opportunity, PortfolioItem


class StrategyService:
    """Service para geração de estratégias."""

    def generate_strategy(
        self,
        cash_available: float,
        current_portfolio: List[PortfolioItem],
        goals: List[Goal],
        opportunities: List[Opportunity],
        portfolio_evaluation: dict = None,
    ) -> dict:
        """Gera estratégia de investimento personalizada."""
        return build_investment_strategy(
            cash_available=cash_available,
            current_portfolio=current_portfolio,
            goals=goals,
            opportunities=opportunities,
            portfolio_evaluation=portfolio_evaluation,
        )
