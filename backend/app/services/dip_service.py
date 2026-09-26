import asyncio
import logging

from app.analysis.classify import auto_category
from app.analysis.decision import confidence_label, decide
from app.core.universe import get_universe
from app.models import AssetType, DipScanItem, DipScannerResponse
from app.repositories import AssetRepository, PortfolioRepository
from app.services.valuation import fair_price_for

logger = logging.getLogger(__name__)

MIN_DROP_PCT = 15.0


def drop_from_high_pct(price: float | None, high_52w: float | None) -> float | None:
    if not price or not high_52w or high_52w <= 0:
        return None
    return round(max(0.0, (high_52w - price) / high_52w * 100), 2)


def _ordem(item: DipScanItem) -> tuple:
    return (
        item.margin_of_safety is None,
        -(item.margin_of_safety or 0.0),
        -item.drop_from_52w_high_pct,
    )


class DipService:
    def __init__(self):
        self.asset_repo = AssetRepository()
        self.portfolio_repo = PortfolioRepository()

    async def scan_dips(
        self,
        universe: str | None = None,
        min_drop: float = MIN_DROP_PCT,
        top: int = 12,
        category: str | None = None,
    ) -> DipScannerResponse:
        if universe:
            tickers = [t.strip().upper() for t in universe.split(",") if t.strip()]
        else:
            tickers = await asyncio.to_thread(get_universe)

        prefs = self.portfolio_repo.get_preferences()
        sem = asyncio.Semaphore(5)

        async def _scan_one(ticker: str) -> DipScanItem | None:
            async with sem:
                try:
                    snap = await self.asset_repo.get_asset(ticker)
                    if not snap or not snap.price:
                        return None

                    queda = drop_from_high_pct(snap.price, snap.fifty_two_week_high)
                    if queda is None or queda < min_drop:
                        return None

                    dividends = await self.asset_repo.get_dividends(ticker)
                    fair = fair_price_for(snap, dividends, prefs)
                    dec = decide(fair, None, current_price=snap.price)

                    return DipScanItem(
                        symbol=snap.symbol,
                        name=snap.name,
                        asset_type=AssetType(snap.asset_type),
                        sector=snap.sector,
                        price=snap.price,
                        as_of=snap.as_of or None,
                        drop_from_52w_high_pct=queda,
                        verdict=dec.verdict,
                        label=dec.label,
                        basis=dec.basis,
                        confidence_label=confidence_label(dec.confidence),
                        band_quality=fair.band_quality,
                        fair_low=fair.fair_low,
                        fair_high=fair.fair_high,
                        principal_value=fair.principal_value,
                        margin_of_safety=fair.margin_of_safety,
                        dividend_yield=snap.dividend_yield,
                        top_reason=dec.reasons[0] if dec.reasons else "",
                    )

                except Exception as exc:
                    logger.warning("Varredura de quedas falhou para %s: %s", ticker, exc)
                    return None

        results = await asyncio.gather(*[_scan_one(t) for t in tickers])
        items = [r for r in results if r is not None]

        if category:
            items = [
                item
                for item in items
                if auto_category(str(getattr(item.asset_type, "value", item.asset_type)))
                == category
            ]

        items.sort(key=_ordem)

        return DipScannerResponse(
            items=items[:top],
            scanned=len(tickers),
            universe_used=tickers,
            min_drop_pct=min_drop,
        )
