"""Service para análise de dividendos."""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

from app.analysis.fair_price import average_dividend_last_n_years, bazin_fair_price
from app.core.config import get_settings
from app.models import DividendRankingItem, DividendRankingResponse
from app.repositories import AssetRepository


class DividendService:
    """Service para operações relacionadas a dividendos."""

    def __init__(self):
        self.asset_repo = AssetRepository()

    async def get_dividend_ranking(
        self,
        universe: Optional[str] = None,
        top: int = 15,
    ) -> DividendRankingResponse:
        """Retorna ranking de ativos por dividend yield."""
        settings = get_settings()

        if universe:
            tickers = [t.strip().upper() for t in universe.split(",") if t.strip()]
        else:
            tickers = settings.universe

        cutoff = datetime.utcnow() - timedelta(days=365)

        async def _one(tk: str) -> Optional[DividendRankingItem]:
            snap = await self.asset_repo.get_asset(tk)
            if not snap or not snap.price:
                return None

            divs = await self.asset_repo.get_dividends(tk)

            total_12m = 0.0
            for d in divs:
                try:
                    dt = datetime.strptime(d["date"], "%Y-%m-%d")
                except Exception:
                    continue
                if dt >= cutoff:
                    total_12m += float(d.get("value", 0.0))

            dy = (total_12m / snap.price * 100) if snap.price > 0 else 0.0

            bazin = None
            if divs:
                avg = average_dividend_last_n_years(divs, 5)
                bazin = bazin_fair_price(avg, 0.06)

            verdict = None
            if bazin and snap.price:
                mos = (bazin - snap.price) / bazin
                if mos >= 0.15:
                    verdict = "Comprar"
                elif mos <= -0.15:
                    verdict = "Vender"
                else:
                    verdict = "Manter"

            return DividendRankingItem(
                ticker=snap.symbol,
                name=snap.name,
                sector=snap.sector,
                price=snap.price,
                dividend_yield_12m=round(dy, 2),
                total_dividends_12m=round(total_12m, 4),
                fair_price_bazin=bazin,
                verdict=verdict,
            )

        raw = await asyncio.gather(*[_one(t) for t in tickers])
        items = [r for r in raw if r and (r.dividend_yield_12m or 0) > 0]
        items.sort(key=lambda x: x.dividend_yield_12m or 0, reverse=True)

        return DividendRankingResponse(items=items[:top])
