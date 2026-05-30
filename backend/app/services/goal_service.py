"""Service para gestão de goals com cálculo de progresso."""

from app.models import Goal
from app.repositories import PortfolioRepository

_DEFAULT_GOALS = [
    {"category": "renda_fixa", "target_pct": 30.0, "target_value": None, "deadline": None},
    {"category": "acoes_br", "target_pct": 35.0, "target_value": None, "deadline": None},
    {"category": "acoes_int", "target_pct": 15.0, "target_value": None, "deadline": None},
    {"category": "fiis", "target_pct": 15.0, "target_value": None, "deadline": None},
    {"category": "cripto", "target_pct": 5.0, "target_value": None, "deadline": None},
]


class GoalService:
    def __init__(self):
        self.repo = PortfolioRepository()

    def get_goals(self) -> list[Goal]:
        data = self.repo.list_goals()
        if not data:
            return [Goal(**g) for g in _DEFAULT_GOALS]
        return [Goal(**g) for g in data]

    def save_goals(self, goals: list[Goal]) -> list[Goal]:
        self.repo.replace_goals([g.dict() for g in goals])
        return self.get_goals()
