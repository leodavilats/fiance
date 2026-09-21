import asyncio
import logging
import time
from dataclasses import dataclass

from app.analysis.classify import auto_category
from app.analysis.decision import confidence_label, decide
from app.analysis.fair_price import (
    FairPriceInputs,
    TechnicalSnapshot,
    compute_fair_price_inputs,
    compute_technical,
    desired_yield_for,
    discount_rate_from,
    fair_price_from_inputs,
)
from app.analysis.score_ruler import is_highlight
from app.analysis.scoring import score_opportunity
from app.collectors.rates import get_rates
from app.collectors.universal import prefetch_brapi_raw
from app.core import cache
from app.core.context import memoize_request
from app.core.pregao import em_pregao
from app.core.universe import get_universe
from app.models import AssetType, OpportunitiesResponse, Opportunity
from app.models.enums import RiskProfile
from app.repositories import AssetRepository, PortfolioRepository


def _taxa_de_desconto() -> float:
    return discount_rate_from(get_rates().get("selic_anual"))


logger = logging.getLogger(__name__)

_SCAN_CACHE_KEY = "opps_market_scan_v2"
_SCAN_TTL = 20 * 60

_SCAN_STALE_TOLERANCE = 72 * 3600

_scan_lock = asyncio.Lock()
_refresh_lock = asyncio.Lock()
_refresh_task: asyncio.Task | None = None


@dataclass
class _MarketRecord:
    ticker: str
    name: str | None
    asset_type: str
    sector: str | None
    price: float
    dividend_yield: float | None
    roe: float | None
    profit_margin: float | None
    debt_to_equity: float | None
    revenue_growth: float | None
    market_cap: float | None
    has_dividend_history: bool
    fair_inputs: FairPriceInputs
    technical: TechnicalSnapshot
    as_of: float = 0.0
    change_percent_day: float | None = None

    def to_dict(self) -> dict:
        data = self.__dict__.copy()
        data["fair_inputs"] = self.fair_inputs.to_dict()
        data["technical"] = self.technical.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "_MarketRecord":
        data = dict(data)
        data["fair_inputs"] = FairPriceInputs(**data["fair_inputs"])
        data["technical"] = TechnicalSnapshot(**data["technical"])
        return cls(**data)


class OpportunityService:
    def __init__(self):
        self.asset_repo = AssetRepository()
        self.portfolio_repo = PortfolioRepository()

    async def _fetch_market_record(self, symbol: str) -> _MarketRecord | None:
        try:
            snap = await self.asset_repo.get_asset(symbol)
        except Exception as exc:
            logger.warning("Falha ao buscar dados de %s: %s", symbol, exc)
            return None

        if not snap or not snap.price:
            return None

        try:
            dividends, history = await asyncio.gather(
                self.asset_repo.get_dividends(symbol),
                self.asset_repo.get_history(symbol, period="2y"),
            )
        except Exception as exc:
            logger.warning("Falha ao buscar histórico de %s: %s", symbol, exc)
            return None

        return _MarketRecord(
            ticker=snap.symbol,
            name=snap.name,
            asset_type=str(snap.asset_type),
            sector=snap.sector,
            price=snap.price,
            dividend_yield=snap.dividend_yield,
            roe=snap.roe,
            profit_margin=snap.profit_margin,
            debt_to_equity=snap.debt_to_equity,
            revenue_growth=snap.revenue_growth,
            market_cap=snap.market_cap,
            has_dividend_history=bool(dividends),
            as_of=snap.as_of,
            change_percent_day=snap.change_percent_day,
            fair_inputs=compute_fair_price_inputs(
                price=snap.price,
                eps=snap.eps,
                book_value=snap.book_value,
                dividends=dividends,
                asset_type=snap.asset_type,
                revenue_growth_pct=snap.revenue_growth,
                pb_ratio=snap.pb_ratio,
                discount_rate=_taxa_de_desconto(),
            ),
            technical=compute_technical(history, snap.fifty_two_week_high, snap.fifty_two_week_low),
        )

    def _build_opportunity(self, record: _MarketRecord, prefs: dict | None = None) -> Opportunity:
        prefs = prefs or {}

        fair = fair_price_from_inputs(
            record.fair_inputs,
            desired_yield=desired_yield_for(record.asset_type, prefs),
        )
        tech = record.technical
        dec = decide(fair, tech, current_price=record.price)

        profile = RiskProfile(prefs.get("risk_profile") or "moderate")

        score, breakdown = score_opportunity(
            asset_type=record.asset_type,
            margin_of_safety=fair.margin_of_safety,
            dividend_yield=record.dividend_yield,
            roe=record.roe,
            profit_margin=record.profit_margin,
            debt_to_equity=record.debt_to_equity,
            revenue_growth=record.revenue_growth,
            market_cap=record.market_cap,
            rsi_14=tech.rsi_14,
            trend=tech.trend,
            profile=profile,
        )

        return Opportunity(
            ticker=record.ticker,
            name=record.name,
            asset_type=AssetType(record.asset_type),
            sector=record.sector,
            price=record.price,
            as_of=record.as_of or None,
            fair_price=fair.consensus,
            fair_low=fair.fair_low,
            fair_high=fair.fair_high,
            band_quality=fair.band_quality,
            independent_inputs=fair.independent_inputs,
            bazin=fair.bazin,
            graham=fair.graham,
            pvp=fair.pvp,
            margin_of_safety=fair.margin_of_safety,
            dividend_yield=record.dividend_yield,
            verdict=dec.verdict,
            label=dec.label,
            basis=dec.basis,
            confidence=dec.confidence,
            confidence_label=confidence_label(dec.confidence),
            data_years=fair.data_years,
            consensus_methods=fair.consensus_methods,
            trend_basis=tech.trend_basis,
            category_resolved=auto_category(
                record.asset_type, record.dividend_yield, record.has_dividend_history
            ),
            score=score,
            score_breakdown=breakdown,
            data_completeness=breakdown.get("data_completeness", 1.0),
            change_percent_day=record.change_percent_day,
            distance_from_52w_high_pct=tech.distance_from_52w_high_pct,
            range_52w_position=tech.range_52w_position,
            reasons=dec.reasons,
        )

    @staticmethod
    def _decode(cached: dict) -> tuple[list[_MarketRecord], int]:
        return (
            [_MarketRecord.from_dict(r) for r in cached["items"]],
            cached["universe_size"],
        )

    async def _scan_market(self) -> tuple[list[_MarketRecord], int]:
        cached, stale_by = cache.get_with_age(_SCAN_CACHE_KEY)

        if cached is not None and stale_by == 0:
            return self._decode(cached)

        if cached is not None and stale_by is not None and stale_by <= _SCAN_STALE_TOLERANCE:
            await self._schedule_refresh()
            logger.info("Servindo scan vencido há %.0f s enquanto recalcula.", stale_by)
            return self._decode(cached)

        return await self._refresh_market()

    async def _schedule_refresh(self) -> None:
        global _refresh_task

        async with _refresh_lock:
            if _refresh_task is not None and not _refresh_task.done():
                return

            async def _run() -> None:
                try:
                    await self._refresh_market()
                except Exception:
                    logger.warning("Falha ao revalidar scan em background", exc_info=True)

            _refresh_task = asyncio.create_task(_run(), name="opps-scan-refresh")

    async def _refresh_market(self) -> tuple[list[_MarketRecord], int]:
        async with _scan_lock:
            cached, stale_by = cache.get_with_age(_SCAN_CACHE_KEY)
            if cached is not None and stale_by == 0:
                return self._decode(cached)

            if cached is not None and not em_pregao():
                logger.info(
                    "Fora do pregão: servindo scan de %.0f s atrás em vez de varrer.",
                    stale_by or 0.0,
                )
                return self._decode(cached)

            universe = sorted(set(await asyncio.to_thread(get_universe)))
            universe_size = len(universe)

            await asyncio.to_thread(prefetch_brapi_raw, universe)

            raws = await asyncio.gather(
                *[self._fetch_market_record(t) for t in universe],
                return_exceptions=True,
            )

            records = []
            for ticker, result in zip(universe, raws, strict=True):
                if isinstance(result, _MarketRecord):
                    records.append(result)
                elif isinstance(result, Exception):
                    logger.warning("Scan falhou para %s: %s", ticker, result)

            failed_count = universe_size - len(records)
            if failed_count > 0:
                logger.info(
                    "Análise de oportunidades: %d/%d ativos falharam na coleta",
                    failed_count,
                    universe_size,
                )

            cache.set(
                _SCAN_CACHE_KEY,
                {
                    "items": [r.to_dict() for r in records],
                    "universe_size": universe_size,
                },
                _SCAN_TTL,
            )
            return records, universe_size

    async def _scan_universe(self, prefs: dict) -> tuple[list[Opportunity], int]:
        records, universe_size = await self._scan_market()
        return [self._build_opportunity(r, prefs) for r in records], universe_size

    async def market_data_age_seconds(self) -> float | None:
        records, _ = await self._scan_market()
        stamps = [r.as_of for r in records if r.as_of]
        if not stamps:
            return None
        return max(0.0, time.time() - min(stamps))

    async def scan_for_current_user(self) -> tuple[list[Opportunity], int]:

        async def _build() -> tuple[list[Opportunity], int]:
            prefs = self.portfolio_repo.get_preferences()
            return await self._scan_universe(prefs)

        return await memoize_request("opportunities.scan", _build)

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
        trend_day: str = "",
        trend_year: str = "",
    ) -> OpportunitiesResponse:
        prefs = self.portfolio_repo.get_preferences()

        held = {p["ticker"].upper() for p in self.portfolio_repo.list_positions()}

        scanned, universe_size = await self.scan_for_current_user()
        scanned_count = len(scanned)
        opps = [o.model_copy() for o in scanned]

        if not include_held and not search:
            opps = [o for o in opps if o.ticker.upper() not in held]

        excluded_tickers = {t.upper() for t in prefs.get("excluded_tickers", [])}
        if excluded_tickers:
            opps = [o for o in opps if o.ticker.upper() not in excluded_tickers]

        preferred_categories = set(prefs.get("preferred_categories", []))
        preferred_sectors = set(prefs.get("preferred_sectors", []))
        if preferred_categories or preferred_sectors:
            for o in opps:
                boost = 0.0
                if o.category_resolved in preferred_categories:
                    boost += 5.0
                if o.sector and o.sector in preferred_sectors:
                    boost += 3.0
                if boost:
                    o.score = round(min(100.0, o.score + boost), 2)

        for o in opps:
            o.in_portfolio = o.ticker.upper() in held
            o.is_interesting = is_highlight(o.verdict, o.score, o.dividend_yield)

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

        if trend_day in ("up", "down"):
            subindo = trend_day == "up"
            opps = [
                o
                for o in opps
                if o.change_percent_day is not None
                and (o.change_percent_day > 0 if subindo else o.change_percent_day < 0)
            ]

        if trend_year in ("up", "down"):
            alta = trend_year == "up"
            opps = [
                o
                for o in opps
                if o.range_52w_position is not None
                and (o.range_52w_position >= 0.5 if alta else o.range_52w_position < 0.5)
            ]

        reverse = sort_order.lower() == "desc"
        if sort_by == "score":
            opps.sort(key=lambda x: x.score, reverse=reverse)
        elif sort_by == "dy":
            opps.sort(key=lambda x: x.dividend_yield or 0, reverse=reverse)
        elif sort_by == "mos":
            opps.sort(key=lambda x: x.margin_of_safety or 0, reverse=reverse)
        elif sort_by == "price":
            opps.sort(key=lambda x: x.price or 0, reverse=reverse)
        elif sort_by == "change_day":
            opps.sort(key=lambda x: x.change_percent_day or 0, reverse=reverse)
        elif sort_by == "range_52w":
            opps.sort(key=lambda x: x.range_52w_position or 0, reverse=reverse)
        else:
            opps.sort(key=lambda x: x.score, reverse=True)

        total_items = len(opps)
        total_pages = (total_items + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_list = opps[start_idx:end_idx]

        return OpportunitiesResponse(
            items=paginated_list,
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
            universe_size=universe_size,
            failed_count=universe_size - scanned_count,
        )
