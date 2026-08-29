from __future__ import annotations

from app.storage import portfolio_store
from app.storage.portfolio_store import (
    ClosedTrade,
    DeviceToken,
    FixedIncomeRow,
    Goal,
    Preferences,
    SectorGoal,
    Snapshot,
    StoredItem,
    TaxLossBalance,
)


class PortfolioRepository:
    @staticmethod
    def list_positions() -> list[StoredItem]:
        return portfolio_store.list_positions()

    @staticmethod
    def replace_all(items: list[StoredItem]) -> None:
        portfolio_store.replace_all(items)

    @staticmethod
    def upsert_position(
        ticker: str, quantity: float, avg_price: float, category: str = "auto"
    ) -> None:
        portfolio_store.upsert_position(ticker, quantity, avg_price, category)

    @staticmethod
    def delete_position(ticker: str) -> None:
        portfolio_store.delete_position(ticker)

    @staticmethod
    def get_position(ticker: str) -> StoredItem | None:
        return portfolio_store.get_position(ticker)

    @staticmethod
    def reduce_position_quantity(ticker: str, sold_qty: float) -> None:
        portfolio_store.reduce_position_quantity(ticker, sold_qty)

    @staticmethod
    def realized_gross_profit_between(start: float, end: float) -> float:
        return portfolio_store.realized_gross_profit_between(start, end)

    @staticmethod
    def list_dividends_received() -> list:
        return portfolio_store.list_dividends_received()

    @staticmethod
    def closed_trades_totals() -> dict:
        return portfolio_store.closed_trades_totals()

    @staticmethod
    def lock_tenant() -> None:
        portfolio_store.lock_tenant()

    @staticmethod
    def sum_gross_sales_in_month(category: str, at: float | None = None) -> float:
        return portfolio_store.sum_gross_sales_in_month(category, at=at)

    @staticmethod
    def create_closed_trade(**kwargs) -> ClosedTrade:
        return portfolio_store.create_closed_trade(**kwargs)

    @staticmethod
    def list_closed_trades(
        limit: int | None = None, cursor: str | None = None
    ) -> list[ClosedTrade]:
        return portfolio_store.list_closed_trades(limit=limit, cursor=cursor)

    @staticmethod
    def tax_loss_balances() -> list[TaxLossBalance]:
        return portfolio_store.tax_loss_balances()

    @staticmethod
    def available_tax_loss(category: str) -> float:
        return portfolio_store.available_tax_loss(category)

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
    def list_snapshots(limit: int = 90) -> list[Snapshot]:
        return portfolio_store.list_snapshots(limit=limit)

    @staticmethod
    def last_updated() -> float | None:
        return portfolio_store.last_updated()

    @staticmethod
    def list_goals() -> list[Goal]:
        return portfolio_store.list_goals()

    @staticmethod
    def replace_goals(goals: list[Goal]) -> None:
        portfolio_store.replace_goals(goals)

    @staticmethod
    def list_sector_goals() -> list[SectorGoal]:
        return portfolio_store.list_sector_goals()

    @staticmethod
    def replace_sector_goals(goals: list[SectorGoal]) -> None:
        portfolio_store.replace_sector_goals(goals)

    @staticmethod
    def get_preferences() -> Preferences:
        return portfolio_store.get_preferences()

    @staticmethod
    def set_preferences(**fields) -> None:
        portfolio_store.set_preferences(**fields)

    @staticmethod
    def list_fixed_income() -> list[FixedIncomeRow]:
        return portfolio_store.list_fixed_income()

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
    def list_all_device_tokens() -> list[DeviceToken]:
        return portfolio_store.list_all_device_tokens()

    @staticmethod
    def list_device_tokens() -> list[DeviceToken]:
        return portfolio_store.list_device_tokens()

    @staticmethod
    def get_notified_opportunity_tickers(user_id: str) -> set[str]:
        return portfolio_store.get_notified_opportunity_tickers(user_id)

    @staticmethod
    def mark_opportunities_notified(user_id: str, tickers: list[str]) -> None:
        portfolio_store.mark_opportunities_notified(user_id, tickers)
