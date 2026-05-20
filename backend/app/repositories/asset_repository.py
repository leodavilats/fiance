"""Repository para acesso a dados de ativos."""

from typing import List, Optional

from app.collectors.b3 import fetch_history, fetch_universe
from app.collectors.news import fetch_news
from app.collectors.universal import (
    fetch_asset,
    fetch_dividends,
    fetch_history_universal,
)


class AssetRepository:
    """Repository para operações de dados de ativos."""

    @staticmethod
    async def get_asset(symbol: str):
        """Busca informações de um ativo."""
        return await fetch_asset(symbol)

    @staticmethod
    async def get_dividends(symbol: str):
        """Busca histórico de dividendos de um ativo."""
        return await fetch_dividends(symbol)

    @staticmethod
    async def get_history(symbol: str, period: str = "2y"):
        """Busca histórico de preços de um ativo."""
        return await fetch_history_universal(symbol, period=period)

    @staticmethod
    async def get_news(symbol: str, asset_type: str, company_name: str = ""):
        """Busca notícias relacionadas a um ativo."""
        return await fetch_news(symbol, asset_type=asset_type, company_name=company_name)

    @staticmethod
    async def get_universe(tickers: List[str]):
        """Busca dados de múltiplos ativos do universo B3."""
        return await fetch_universe(tickers)

    @staticmethod
    async def get_b3_history(tickers: List[str]):
        """Busca histórico de preços de múltiplos ativos B3."""
        return await fetch_history(tickers)
