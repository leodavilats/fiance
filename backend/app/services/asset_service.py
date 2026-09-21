import asyncio

from app.analysis.decision import confidence_label, decide
from app.analysis.fair_price import (
    compute_fair_price,
    compute_technical,
    desired_yield_for,
    discount_rate_from,
)
from app.analysis.falsifiers import falsifiers
from app.collectors.rates import get_rates
from app.core.errors import NotFoundError
from app.models import (
    AssetAnalysis,
    AssetType,
    DecisionBlock,
    FairPriceBlock,
    PricePoint,
    TechnicalBlock,
)
from app.repositories import AssetRepository, PortfolioRepository


def _taxa_de_desconto() -> float:
    return discount_rate_from(get_rates().get("selic_anual"))


class AssetService:
    def __init__(self):
        self.asset_repo = AssetRepository()
        self.portfolio_repo = PortfolioRepository()

    async def analyze_asset(
        self, symbol: str, *, include_history: bool = True, personalized: bool = True
    ) -> AssetAnalysis:

        snap = await self.asset_repo.get_asset(symbol)
        if not snap:
            raise NotFoundError(f"Ativo '{symbol}' não encontrado ou sem dados.")

        history, dividends = await asyncio.gather(
            self.asset_repo.get_history(symbol, period="2y"),
            self.asset_repo.get_dividends(symbol),
        )

        prefs = self.portfolio_repo.get_preferences() if personalized else None

        fair = compute_fair_price(
            price=snap.price,
            eps=snap.eps,
            book_value=snap.book_value,
            dividends=dividends,
            asset_type=snap.asset_type,
            week52_high=snap.fifty_two_week_high,
            pb_ratio=snap.pb_ratio,
            revenue_growth_rate=snap.revenue_growth,
            desired_yield=desired_yield_for(snap.asset_type, prefs),
            discount_rate=_taxa_de_desconto(),
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
            as_of=snap.as_of or None,
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
                confidence_label=confidence_label(dec.confidence),
                basis=dec.basis,
                reasons=dec.reasons,
                falsifiers=falsifiers(
                    verdict=dec.verdict,
                    price=snap.price,
                    consensus=fair.consensus,
                    bazin=fair.bazin,
                    consensus_methods=fair.consensus_methods,
                    avg_dividend=fair.avg_dividend_5y,
                    trend=tech.trend,
                    sma_50=tech.sma_50,
                    sma_200=tech.sma_200,
                    rsi_14=tech.rsi_14,
                    band_verdict=dec.band_verdict,
                    fair_low=fair.fair_low,
                    fair_high=fair.fair_high,
                    basis=dec.basis,
                    dcf=fair.dcf,
                    dcf_sem_crescimento=fair.details.get("dcf_sem_crescimento"),
                ),
            ),
            price_history=(
                [
                    PricePoint(date=day, close=close)
                    for day, close in sorted(history.items())
                    if close is not None
                ]
                if include_history
                else []
            ),
        )
