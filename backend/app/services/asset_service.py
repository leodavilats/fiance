import asyncio

from app.analysis.decision import decide
from app.analysis.fair_price import compute_fair_price, compute_technical, desired_yield_for
from app.analysis.falsifiers import falsifiers
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


class AssetService:
    def __init__(self):
        self.asset_repo = AssetRepository()
        self.portfolio_repo = PortfolioRepository()

    async def analyze_asset(
        self, symbol: str, *, include_history: bool = True, personalized: bool = True
    ) -> AssetAnalysis:
        """Análise completa de um ativo.

        `personalized=False` é a análise **impessoal**: sem o yield desejado do
        usuário, portanto sem tocar em preferência nenhuma. É o que a página
        pública renderiza no servidor — ela não tem titular, e a mesma URL
        precisa devolver o mesmo HTML para o robô de busca e para quem chega
        pelo link.

        `include_history` existe para `/compare`: N séries diárias de 2 anos numa
        única resposta são payload puro, e a comparação não desenha gráfico.
        """

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
