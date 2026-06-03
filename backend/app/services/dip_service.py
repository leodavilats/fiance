import asyncio
import logging

from app.analysis.dip_analysis import compute_dip_analysis
from app.analysis.fair_price import compute_fair_price, compute_technical
from app.collectors.news import analyze_news_with_ai, news_sentiment_summary
from app.core.config import get_settings
from app.models import (
    AssetType,
    DipAnalysisResponse,
    DipScanItem,
    DipScannerResponse,
    DipScoreBreakdownSchema,
    FairPriceBlock,
    NewsItemSchema,
    TechnicalBlock,
)
from app.repositories import AssetRepository, PortfolioRepository

logger = logging.getLogger(__name__)


class DipService:
    def __init__(self):
        self.asset_repo = AssetRepository()
        self.portfolio_repo = PortfolioRepository()

    async def analyze_dip(self, symbol: str) -> DipAnalysisResponse:
        snap = await self.asset_repo.get_asset(symbol)
        if not snap:
            raise ValueError(f"Ativo '{symbol}' não encontrado ou sem dados.")

        history, dividends, news_items = await asyncio.gather(
            self.asset_repo.get_history(symbol, period="2y"),
            self.asset_repo.get_dividends(symbol),
            self.asset_repo.get_news(
                symbol, asset_type=snap.asset_type, company_name=snap.name or ""
            ),
        )

        fair = compute_fair_price(
            price=snap.price,
            eps=snap.eps,
            book_value=snap.book_value,
            dividends=dividends,
            asset_type=snap.asset_type,
            week52_high=snap.fifty_two_week_high,
        )

        tech = compute_technical(history, snap.fifty_two_week_high, snap.fifty_two_week_low)
        sentiment_summary = news_sentiment_summary(news_items)

        news_ai_analysis = await analyze_news_with_ai(news_items, symbol, snap.name or "")

        dip = compute_dip_analysis(
            margin_of_safety=fair.margin_of_safety,
            roe=snap.roe,
            profit_margin=snap.profit_margin,
            debt_to_equity=snap.debt_to_equity,
            rsi_14=tech.rsi_14,
            trend=tech.trend,
            distance_from_52w_high_pct=tech.distance_from_52w_high_pct,
            sma_200=tech.sma_200,
            last_price=tech.last_price,
            dividend_yield=snap.dividend_yield,
            avg_dividend_5y=fair.avg_dividend_5y,
            fair_price_consensus=fair.consensus,
            current_price=snap.price,
            news_items=news_items,
            news_sentiment_summary=sentiment_summary,
        )

        return DipAnalysisResponse(
            symbol=snap.symbol,
            asset_type=AssetType(snap.asset_type),
            name=snap.name,
            sector=snap.sector,
            price=snap.price,
            currency=snap.currency,
            fair_price=FairPriceBlock(**fair.__dict__),
            technical=TechnicalBlock(**tech.__dict__),
            fundamentals={
                "pe_ratio": snap.pe_ratio,
                "pb_ratio": snap.pb_ratio,
                "eps": snap.eps,
                "roe": snap.roe,
                "dividend_yield": snap.dividend_yield,
                "debt_to_equity": snap.debt_to_equity,
                "profit_margin": snap.profit_margin,
                "revenue_growth": snap.revenue_growth,
                "market_cap": snap.market_cap,
                "fifty_two_week_high": snap.fifty_two_week_high,
                "fifty_two_week_low": snap.fifty_two_week_low,
            },
            dip_score=dip.dip_score,
            breakdown=DipScoreBreakdownSchema(**dip.breakdown.__dict__),
            verdict=dip.verdict,
            verdict_label=dip.verdict_label,
            confidence=dip.confidence,
            reasons=dip.reasons,
            drop_from_52w_high_pct=dip.drop_from_52w_high_pct,
            drop_from_fair_price_pct=dip.drop_from_fair_price_pct,
            news=[
                NewsItemSchema(
                    title=n.title,
                    source=n.source,
                    published=n.published,
                    url=n.url,
                    sentiment=n.sentiment,
                )
                for n in news_items
            ],
            news_sentiment_summary=dip.news_sentiment_summary,
            news_ai_summary=news_ai_analysis.get("summary"),
            news_ai_score=news_ai_analysis.get("score"),
            news_impact=news_ai_analysis.get("impact"),
            news_key_topics=news_ai_analysis.get("key_topics", []),
        )

    async def scan_dips(
        self,
        universe: str | None = None,
        min_score: float = 40.0,
        top: int = 12,
    ) -> DipScannerResponse:
        settings = get_settings()

        if universe:
            tickers = [t.strip().upper() for t in universe.split(",") if t.strip()]
        else:
            tickers = list(settings.universe)

        sem = asyncio.Semaphore(5)

        async def _scan_one(ticker: str) -> DipScanItem | None:
            async with sem:
                try:
                    snap = await self.asset_repo.get_asset(ticker)
                    if not snap or not snap.price:
                        return None

                    history, dividends = await asyncio.gather(
                        self.asset_repo.get_history(ticker, period="2y"),
                        self.asset_repo.get_dividends(ticker),
                    )

                    fair = compute_fair_price(
                        price=snap.price,
                        eps=snap.eps,
                        book_value=snap.book_value,
                        dividends=dividends,
                        asset_type=snap.asset_type,
                        week52_high=snap.fifty_two_week_high,
                    )

                    tech = compute_technical(
                        history, snap.fifty_two_week_high, snap.fifty_two_week_low
                    )

                    dip = compute_dip_analysis(
                        margin_of_safety=fair.margin_of_safety,
                        roe=snap.roe,
                        profit_margin=snap.profit_margin,
                        debt_to_equity=snap.debt_to_equity,
                        rsi_14=tech.rsi_14,
                        trend=tech.trend,
                        distance_from_52w_high_pct=tech.distance_from_52w_high_pct,
                        sma_200=tech.sma_200,
                        last_price=tech.last_price,
                        dividend_yield=snap.dividend_yield,
                        avg_dividend_5y=fair.avg_dividend_5y,
                        fair_price_consensus=fair.consensus,
                        current_price=snap.price,
                        news_items=[],
                        news_sentiment_summary="",
                    )

                    if dip.dip_score < min_score:
                        return None

                    return DipScanItem(
                        symbol=snap.symbol,
                        name=snap.name,
                        asset_type=AssetType(snap.asset_type),
                        sector=snap.sector,
                        price=snap.price,
                        fair_price_consensus=fair.consensus,
                        margin_of_safety=fair.margin_of_safety,
                        dip_score=dip.dip_score,
                        breakdown=DipScoreBreakdownSchema(**dip.breakdown.__dict__),
                        verdict=dip.verdict,
                        verdict_label=dip.verdict_label,
                        confidence=dip.confidence,
                        drop_from_52w_high_pct=dip.drop_from_52w_high_pct,
                        drop_from_fair_price_pct=dip.drop_from_fair_price_pct,
                        dividend_yield=snap.dividend_yield,
                        rsi_14=tech.rsi_14,
                        top_reason=dip.reasons[0] if dip.reasons else "",
                    )

                except Exception as exc:
                    logger.warning("Dip scan falhou para %s: %s", ticker, exc)
                    return None

        results = await asyncio.gather(*[_scan_one(t) for t in tickers])
        items = [r for r in results if r is not None]
        items.sort(key=lambda x: x.dip_score, reverse=True)

        return DipScannerResponse(
            items=items[:top],
            scanned=len(tickers),
            universe_used=tickers,
        )
