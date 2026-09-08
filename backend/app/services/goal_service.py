from app.models import Goal, SectorGoal
from app.repositories import PortfolioRepository

_DEFAULT_GOALS = [
    {"category": "renda_fixa", "target_pct": 30.0, "target_value": None, "deadline": None},
    {"category": "acoes_br", "target_pct": 35.0, "target_value": None, "deadline": None},
    {"category": "bdrs", "target_pct": 15.0, "target_value": None, "deadline": None},
    {"category": "fiis", "target_pct": 15.0, "target_value": None, "deadline": None},
    {"category": "etfs", "target_pct": 5.0, "target_value": None, "deadline": None},
]

_DEFAULT_SECTOR_GOALS = [
    {"sector": "Financeiro", "target_pct": 20.0},
    {"sector": "Energia", "target_pct": 15.0},
    {"sector": "Varejo", "target_pct": 15.0},
    {"sector": "Tecnologia", "target_pct": 20.0},
    {"sector": "Saúde", "target_pct": 10.0},
    {"sector": "Outros", "target_pct": 20.0},
]


class GoalService:
    def __init__(self):
        self.repo = PortfolioRepository()

    def get_goals(self) -> list[Goal]:
        data = self.repo.list_goals()
        if not data:
            return [Goal(**g) for g in _DEFAULT_GOALS]
        return [Goal(**g) for g in data]

    def has_declared_goals(self) -> bool:
        """Se a alocação-alvo é da pessoa, ou o padrão do produto.

        `get_goals` cai num padrão de 30/35/15/15/5 quando não há nada salvo, e telas que só
        precisam de uma régua para desenhar vivem bem com isso. Quem vai **distribuir dinheiro**
        precisa da distinção: sugerir 35% em ações porque o produto acha, e apresentar isso como
        se a pessoa tivesse pedido, é inventar objetivo alheio.
        """
        return bool(self.repo.list_goals())

    def save_goals(self, goals: list[Goal]) -> list[Goal]:
        self.repo.replace_goals([g.dict() for g in goals])
        return self.get_goals()

    def get_sector_goals(self) -> list[SectorGoal]:
        data = self.repo.list_sector_goals()
        if not data:
            return [SectorGoal(**g) for g in _DEFAULT_SECTOR_GOALS]
        return [SectorGoal(**g) for g in data]

    def save_sector_goals(self, goals: list[SectorGoal]) -> list[SectorGoal]:
        self.repo.replace_sector_goals([g.dict() for g in goals])
        return self.get_sector_goals()
