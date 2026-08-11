import asyncio
import logging

from app.analysis.classify import auto_category
from app.analysis.decision import decide
from app.analysis.fair_price import compute_fair_price, compute_technical, desired_yield_for
from app.core import cache
from app.core.universe import get_universe
from app.models import AssetType, OpportunitiesResponse, Opportunity
from app.repositories import AssetRepository, PortfolioRepository

logger = logging.getLogger(__name__)

_SCAN_CACHE_KEY = "opps_full_scan"
_SCAN_TTL = 20 * 60
_scan_lock = asyncio.Lock()


class OpportunityService:
    def __init__(self):
        self.asset_repo = AssetRepository()
        self.portfolio_repo = PortfolioRepository()

    async def _build_opportunity(
        self, symbol: str, prefs: dict | None = None
    ) -> Opportunity | None:
        try:
            snap = await self.asset_repo.get_asset(symbol)
        except Exception as exc:
            logger.warning("Falha ao buscar dados de %s: %s", symbol, exc)
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
            asset_type=snap.asset_type,
            week52_high=snap.fifty_two_week_high,
            pb_ratio=snap.pb_ratio,
            revenue_growth_rate=snap.revenue_growth,
            desired_yield=desired_yield_for(snap.asset_type, prefs),
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
            bazin=fair.bazin,
            graham=fair.graham,
            pvp=fair.pvp,
            margin_of_safety=fair.margin_of_safety,
            dividend_yield=snap.dividend_yield,
            verdict=verdict,
            label=label,
            category_resolved=auto,
            score=score,
            reasons=dec.reasons,
        )

    async def _scan_universe(self, prefs: dict) -> tuple[list[Opportunity], int]:
        cached = cache.get(_SCAN_CACHE_KEY)
        if cached is not None:
            opps = [Opportunity(**o) for o in cached["items"]]
            return opps, cached["universe_size"]

        async with _scan_lock:
            # revalida: outra request pode ter preenchido o cache enquanto esperávamos o lock
            cached = cache.get(_SCAN_CACHE_KEY)
            if cached is not None:
                opps = [Opportunity(**o) for o in cached["items"]]
                return opps, cached["universe_size"]

            universe = set(await asyncio.to_thread(get_universe))
            universe_size = len(universe)
            raws = await asyncio.gather(*[self._build_opportunity(t, prefs) for t in universe])
            opps = [o for o in raws if o is not None]
            failed_count = universe_size - len(opps)
            if failed_count > 0:
                logger.info(
                    "Análise de oportunidades: %d/%d ativos falharam na coleta",
                    failed_count,
                    universe_size,
                )

            cache.set(
                _SCAN_CACHE_KEY,
                {
                    "items": [o.model_dump(mode="json") for o in opps],
                    "universe_size": universe_size,
                },
                _SCAN_TTL,
            )
            return opps, universe_size

    async def get_opportunities(
        self,
        include_held: bool = False,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "score",
        sort_order: str = "desc",
        search: str = "",
        min_dy: float | None = None,
        min_mos: float | None = None,
        sector: str = "",
        asset_type: str = "",
        category: str = "",
        only_interesting: bool = False,
    ) -> OpportunitiesResponse:
        prefs = self.portfolio_repo.get_preferences()
        cash = prefs["cash_available"]

        held = {p["ticker"].upper() for p in self.portfolio_repo.list_positions()}

        scanned, universe_size = await self._scan_universe(prefs)
        opps: list[Opportunity] = [o.model_copy() for o in scanned]

        if not include_held and not search:
            opps = [o for o in opps if o.ticker.upper() not in held]

        for o in opps:
            o.in_portfolio = o.ticker.upper() in held
            o.is_interesting = o.verdict == "STRONG_BUY" or (
                o.score >= 75 and (o.dividend_yield or 0) >= 6.0
            )

        if search:
            search_lower = search.lower()
            opps = [
                o
                for o in opps
                if search_lower in o.ticker.lower() or (o.name and search_lower in o.name.lower())
            ]

        if min_dy is not None and min_dy > 0:
            opps = [o for o in opps if (o.dividend_yield or 0) >= min_dy]

        if min_mos is not None and min_mos != 0:
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
            universe_size=universe_size,
            failed_count=universe_size - len(scanned),
        )
