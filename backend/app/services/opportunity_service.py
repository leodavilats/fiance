"""Service para análise de oportunidades de investimento."""

import asyncio

from app.analysis.classify import auto_category
from app.analysis.decision import decide
from app.analysis.fair_price import compute_fair_price, compute_technical
from app.core.config import get_settings
from app.models import AssetType, OpportunitiesResponse, Opportunity
from app.repositories import AssetRepository, PortfolioRepository


class OpportunityService:
    """Service para identificação de oportunidades."""

    def __init__(self):
        self.asset_repo = AssetRepository()
        self.portfolio_repo = PortfolioRepository()

    async def _build_opportunity(
        self, symbol: str, desired_yield: float = 0.06
    ) -> Opportunity | None:
        """Constrói uma oportunidade a partir de um símbolo."""
        try:
            snap = await self.asset_repo.get_asset(symbol)
        except Exception:
            return None

        if not snap or not snap.price:
            return None

        dividends = await self.asset_repo.get_dividends(symbol)
        history = await self.asset_repo.get_history(symbol, period="1y")

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

        auto = auto_category(snap.asset_type, snap.dividend_yield, bool(dividends))

        mos = fair.margin_of_safety or 0.0
        dy_pct = snap.dividend_yield or 0.0
        rsi = tech.rsi_14 if tech.rsi_14 is not None else 50.0

        rsi_bonus = max(0.0, (60.0 - rsi) / 40.0)
        trend_bonus = (
            5.0 if tech.trend == "uptrend" else (-5.0 if tech.trend == "downtrend" else 0.0)
        )

        score = round((mos * 60) + (dy_pct * 1.5) + (rsi_bonus * 10) + trend_bonus, 2)

        verdict = dec.verdict
        label = dec.label

        if snap.asset_type == "crypto" and verdict == "UNKNOWN":
            if tech.trend == "uptrend" and rsi < 70:
                verdict, label = "BUY", "Comprar (momentum)"
            elif tech.trend == "downtrend" and rsi > 30:
                verdict, label = "SELL", "Evitar (tendência ruim)"
            elif rsi <= 30:
                verdict, label = "BUY", "Comprar (sobrevendido)"
            elif rsi >= 70:
                verdict, label = "HOLD", "Aguardar (sobrecomprado)"
            else:
                verdict, label = "HOLD", "Manter"

        return Opportunity(
            ticker=snap.symbol,
            name=snap.name,
            asset_type=AssetType(snap.asset_type),
            sector=snap.sector,
            price=snap.price,
            fair_price=fair.consensus,
            margin_of_safety=fair.margin_of_safety,
            dividend_yield=snap.dividend_yield,
            verdict=verdict,
            label=label,
            category_resolved=auto,
            score=score,
            reasons=dec.reasons,
        )

    async def get_opportunities(
        self,
        include_held: bool = False,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "score",
        sort_order: str = "desc",
        search: str = "",
        min_dy: float = 0,
        min_mos: float = 0,
        sector: str = "",
        asset_type: str = "",
        category: str = "",
        only_interesting: bool = False,
    ) -> OpportunitiesResponse:
        """Retorna lista de oportunidades de investimento."""
        settings = get_settings()
        prefs = self.portfolio_repo.get_preferences()
        cash = prefs["cash_available"]
        desired_yield = prefs["desired_yield"]

        held = {p["ticker"].upper() for p in self.portfolio_repo.list_positions()}
        watch = {w["ticker"].upper() for w in self.portfolio_repo.list_watchlist()}

        universe = set(settings.universe) | watch

        if not include_held:
            universe -= held

        raws = await asyncio.gather(*[self._build_opportunity(t, desired_yield) for t in universe])
        opps: list[Opportunity] = [o for o in raws if o]

        for o in opps:
            o.in_watchlist = o.ticker.upper() in watch
            o.in_portfolio = o.ticker.upper() in held
            o.is_interesting = o.verdict == "STRONG_BUY" or (
                o.score >= 75 and (o.dividend_yield or 0) >= 6.0
            )

        # Aplicar filtros
        if search:
            search_lower = search.lower()
            opps = [
                o
                for o in opps
                if search_lower in o.ticker.lower() or (o.name and search_lower in o.name.lower())
            ]

        if min_dy > 0:
            opps = [o for o in opps if (o.dividend_yield or 0) >= min_dy]

        if min_mos != 0:
            opps = [o for o in opps if (o.margin_of_safety or 0) * 100 >= min_mos]

        if sector:
            opps = [o for o in opps if o.sector == sector]

        if asset_type:
            opps = [o for o in opps if o.asset_type.value == asset_type]

        if category:
            opps = [o for o in opps if o.category_resolved == category]

        if only_interesting:
            opps = [o for o in opps if o.is_interesting]

        reverse = sort_order.lower() == "desc"
        if sort_by == "score":
            opps.sort(key=lambda x: x.score, reverse=reverse)
        elif sort_by == "dy":
            opps.sort(key=lambda x: x.dividend_yield or 0, reverse=reverse)
        elif sort_by == "mos":
            opps.sort(key=lambda x: x.margin_of_safety or 0, reverse=reverse)
        elif sort_by == "price":
            opps.sort(key=lambda x: x.price or 0, reverse=reverse)
        else:
            opps.sort(key=lambda x: x.score, reverse=True)

        total_items = len(opps)
        total_pages = (total_items + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_list = opps[start_idx:end_idx]

        if cash > 0 and paginated_list:
            n_sugg = min(5, len(paginated_list))
            per_asset = cash / n_sugg

            for o in paginated_list[:n_sugg]:
                if o.price and o.price > 0:
                    qty = int(per_asset // o.price)
                    if qty > 0:
                        o.suggested_quantity = qty
                        o.suggested_invest = round(qty * o.price, 2)

        return OpportunitiesResponse(
            items=paginated_list,
            cash_available=cash,
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
        )
