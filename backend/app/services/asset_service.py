import asyncio

from app.analysis.decision import decide
from app.analysis.fair_price import compute_fair_price, compute_technical
from app.models import (
    AssetAnalysis,
    AssetType,
    DecisionBlock,
    FairPriceBlock,
    TechnicalBlock,
)
from app.repositories import AssetRepository


class AssetService:
    def __init__(self):
        self.asset_repo = AssetRepository()

    async def analyze_asset(self, symbol: str, desired_yield: float = 0.06) -> AssetAnalysis:
        snap = await self.asset_repo.get_asset(symbol)
        if not snap:
            raise ValueError(f"Ativo '{symbol}' não encontrado ou sem dados.")

        history, dividends = await asyncio.gather(
            self.asset_repo.get_history(symbol, period="2y"),
            self.asset_repo.get_dividends(symbol),
        )

        fair = compute_fair_price(
            price=snap.price,
            eps=snap.eps,
            book_value=snap.book_value,
            dividends=dividends,
            desired_yield=desired_yield,
            week52_high=snap.fifty_two_week_high,
        )

        tech = compute_technical(history, snap.fifty_two_week_high, snap.fifty_two_week_low)
        dec = decide(fair, tech, current_price=snap.price)

        return AssetAnalysis(
            symbol=snap.symbol,
            asset_type=AssetType(snap.asset_type),
            name=snap.name,
            sector=snap.sector,
            currency=snap.currency,
            price=snap.price,
            fundamentals={
                "market_cap": snap.market_cap,
                "pe_ratio": snap.pe_ratio,
                "pb_ratio": snap.pb_ratio,
                "eps": snap.eps,
                "book_value": snap.book_value,
                "roe": snap.roe,
                "dividend_yield": snap.dividend_yield,
                "debt_to_equity": snap.debt_to_equity,
                "profit_margin": snap.profit_margin,
                "revenue_growth": snap.revenue_growth,
                "fifty_two_week_high": snap.fifty_two_week_high,
                "fifty_two_week_low": snap.fifty_two_week_low,
            },
            fair_price=FairPriceBlock(**fair.__dict__),
            technical=TechnicalBlock(**tech.__dict__),
            decision=DecisionBlock(
                verdict=dec.verdict,
                label=dec.label,
                confidence=dec.confidence,
                reasons=dec.reasons,
            ),
        )
