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
    def get_position(ticker: str) -> dict | None:
        return portfolio_store.get_position(ticker)

    @staticmethod
    def reduce_position_quantity(ticker: str, sold_qty: float) -> None:
        portfolio_store.reduce_position_quantity(ticker, sold_qty)

    @staticmethod
    def sum_gross_sales_this_month(category: str) -> float:
        return portfolio_store.sum_gross_sales_this_month(category)

    @staticmethod
    def create_closed_trade(**kwargs) -> dict:
        return portfolio_store.create_closed_trade(**kwargs)

    @staticmethod
    def list_closed_trades() -> list[dict]:
        return portfolio_store.list_closed_trades()

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
        cash_available: float = 0.0,
        passive_income_goal: float | None = None,
        desired_yield_stock: float | None = None,
        desired_yield_fii: float | None = None,
        desired_yield_bdr: float | None = None,
        desired_yield_etf: float | None = None,
        notify_price_alerts: bool | None = None,
        opportunities_frequency: str | None = None,
        risk_profile: str | None = None,
        preferred_categories: list[str] | None = None,
        preferred_sectors: list[str] | None = None,
        excluded_tickers: list[str] | None = None,
    ) -> None:
        portfolio_store.set_preferences(
            cash_available,
            passive_income_goal,
            desired_yield_stock,
            desired_yield_fii,
            desired_yield_bdr,
            desired_yield_etf,
            notify_price_alerts,
            opportunities_frequency,
            risk_profile,
            preferred_categories,
            preferred_sectors,
            excluded_tickers,
        )

    @staticmethod
    def get_last_digest_sent_at(user_id: str | None = None) -> float | None:
        return portfolio_store.get_last_digest_sent_at(user_id)

    @staticmethod
    def mark_digest_sent(sent_at: float, user_id: str | None = None) -> None:
        portfolio_store.mark_digest_sent(sent_at, user_id)

    @staticmethod
    def register_device_token(token: str, platform: str = "android") -> None:
        portfolio_store.register_device_token(token, platform)

    @staticmethod
    def unregister_device_token(token: str) -> None:
        portfolio_store.unregister_device_token(token)

    @staticmethod
    def list_all_device_tokens() -> list[dict]:
        return portfolio_store.list_all_device_tokens()

    @staticmethod
    def list_device_tokens() -> list[dict]:
        return portfolio_store.list_device_tokens()

    @staticmethod
    def get_notified_opportunity_tickers(user_id: str) -> set[str]:
        return portfolio_store.get_notified_opportunity_tickers(user_id)

    @staticmethod
    def mark_opportunities_notified(user_id: str, tickers: list[str]) -> None:
        portfolio_store.mark_opportunities_notified(user_id, tickers)

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
