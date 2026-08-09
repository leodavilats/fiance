from app.storage import portfolio_store


class PortfolioRepository:
    @staticmethod
    def list_positions() -> list[dict]:
        return portfolio_store.list_positions()

    @staticmethod
    def replace_all(items: list[dict]) -> None:
        portfolio_store.replace_all(items)

    @staticmethod
    def delete_position(ticker: str) -> None:
        portfolio_store.delete_position(ticker)

    @staticmethod
    def record_snapshot(
        total_invested: float,
        total_current: float,
        total_pnl: float,
        total_pnl_pct: float,
    ) -> None:
        portfolio_store.record_snapshot(
            total_invested=total_invested,
            total_current=total_current,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
        )

    @staticmethod
    def list_snapshots(limit: int = 90) -> list[dict]:
        return portfolio_store.list_snapshots(limit=limit)

    @staticmethod
    def last_updated() -> float | None:
        return portfolio_store.last_updated()

    @staticmethod
    def list_goals() -> list[dict]:
        return portfolio_store.list_goals()

    @staticmethod
    def replace_goals(goals: list[dict]) -> None:
        portfolio_store.replace_goals(goals)

    @staticmethod
    def get_preferences() -> dict:
        return portfolio_store.get_preferences()

    @staticmethod
    def set_preferences(
        cash_available: float,
        passive_income_goal: float | None = None,
        desired_yield_stock: float | None = None,
        desired_yield_fii: float | None = None,
        desired_yield_int: float | None = None,
    ) -> None:
        portfolio_store.set_preferences(
            cash_available,
            passive_income_goal,
            desired_yield_stock,
            desired_yield_fii,
            desired_yield_int,
        )

    @staticmethod
    def list_sector_goals() -> list[dict]:
        return portfolio_store.list_sector_goals()

    @staticmethod
    def replace_sector_goals(goals: list[dict]) -> None:
        portfolio_store.replace_sector_goals(goals)

    @staticmethod
    def list_watchlist() -> list[dict]:
        return portfolio_store.list_watchlist()

    @staticmethod
    def replace_watchlist(items: list[dict]) -> None:
        portfolio_store.replace_watchlist(items)

    @staticmethod
    def remove_watchlist(ticker: str) -> None:
        portfolio_store.remove_watchlist(ticker)
