"""Repository para acesso a dados de portfolio."""

from typing import List, Optional

from app.storage import portfolio_store


class PortfolioRepository:
    """Repository para operações de dados de portfolio."""

    @staticmethod
    def list_positions() -> List[dict]:
        """Lista todas as posições do portfolio."""
        return portfolio_store.list_positions()

    @staticmethod
    def replace_all(items: List[dict]) -> None:
        """Substitui todas as posições do portfolio."""
        portfolio_store.replace_all(items)

    @staticmethod
    def delete_position(ticker: str) -> None:
        """Remove uma posição do portfolio."""
        portfolio_store.delete_position(ticker)

    @staticmethod
    def record_snapshot(
        total_invested: float,
        total_current: float,
        total_pnl: float,
        total_pnl_pct: float,
    ) -> None:
        """Registra um snapshot do portfolio."""
        portfolio_store.record_snapshot(
            total_invested=total_invested,
            total_current=total_current,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
        )

    @staticmethod
    def list_snapshots(limit: int = 90) -> List[dict]:
        """Lista snapshots do portfolio."""
        return portfolio_store.list_snapshots(limit=limit)

    @staticmethod
    def last_updated() -> Optional[float]:
        """Retorna timestamp da última atualização."""
        return portfolio_store.last_updated()

    @staticmethod
    def list_watchlist() -> List[dict]:
        """Lista itens da watchlist."""
        return portfolio_store.list_watchlist()

    @staticmethod
    def replace_watchlist(items: List[dict]) -> None:
        """Substitui a watchlist."""
        portfolio_store.replace_watchlist(items)

    @staticmethod
    def remove_watchlist(ticker: str) -> None:
        """Remove item da watchlist."""
        portfolio_store.remove_watchlist(ticker)

    @staticmethod
    def list_goals() -> List[dict]:
        """Lista goals de alocação."""
        return portfolio_store.list_goals()

    @staticmethod
    def replace_goals(goals: List[dict]) -> None:
        """Substitui goals de alocação."""
        portfolio_store.replace_goals(goals)

    @staticmethod
    def get_preferences() -> dict:
        """Retorna preferências do usuário."""
        return portfolio_store.get_preferences()

    @staticmethod
    def set_preferences(cash_available: float, desired_yield: float) -> None:
        """Define preferências do usuário."""
        portfolio_store.set_preferences(cash_available, desired_yield)
