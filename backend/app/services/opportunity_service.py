import asyncio
import logging
from dataclasses import dataclass

from app.analysis.classify import auto_category
from app.analysis.decision import decide
from app.analysis.fair_price import (
    FairPriceInputs,
    TechnicalSnapshot,
    compute_fair_price_inputs,
    compute_technical,
    desired_yield_for,
    fair_price_from_inputs,
)
from app.analysis.score_ruler import is_highlight
from app.analysis.scoring import score_opportunity
from app.core import cache
from app.core.context import memoize_request
from app.core.universe import get_universe
from app.models import AssetType, OpportunitiesResponse, Opportunity
from app.models.enums import RiskProfile
from app.repositories import AssetRepository, PortfolioRepository

logger = logging.getLogger(__name__)

# v2: o cache guarda **dado de mercado** por ticker, não o resultado já
# personalizado. Antes a chave era global (`opps_full_scan`) mas o valor
# cacheado dependia de desired_yield/risk_profile do primeiro usuário a
# aquecê-la: as metas de yield da tela de Configurações não tinham efeito e o
# usuário B via preço justo e score calculados com as preferências do usuário A.
_SCAN_CACHE_KEY = "opps_market_scan_v2"
_SCAN_TTL = 20 * 60

# Até quanto tempo depois do vencimento vale servir o scan antigo enquanto um
# novo roda em background. Um scan são ~280 tickers × httpx com timeout de 15 s:
# fazer o usuário esperar por isso dentro de um GET /dashboard é a diferença
# entre a tela abrir em milissegundos e abrir em minutos. Dado de mercado com
# algumas horas de atraso é muito melhor que um dashboard travado.
_SCAN_STALE_TOLERANCE = 12 * 3600

_scan_lock = asyncio.Lock()
_refresh_lock = asyncio.Lock()
_refresh_task: asyncio.Task | None = None


@dataclass
class _MarketRecord:
    """Insumos de um ticker que não dependem de preferência do usuário."""

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

        # get_dividends e get_history derivam do mesmo payload bruto da BRAPI e
        # não dependem um do outro — em série pagavam 3x a latência de cache miss.
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
            fair_inputs=compute_fair_price_inputs(
                price=snap.price,
                eps=snap.eps,
                book_value=snap.book_value,
                dividends=dividends,
                asset_type=snap.asset_type,
                revenue_growth_pct=snap.revenue_growth,
                pb_ratio=snap.pb_ratio,
            ),
            technical=compute_technical(history, snap.fifty_two_week_high, snap.fifty_two_week_low),
        )

    def _build_opportunity(self, record: _MarketRecord, prefs: dict | None = None) -> Opportunity:
        """Aplica preferências sobre dado de mercado já coletado. CPU pura."""
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

        verdict = dec.verdict
        label = dec.label

        if record.asset_type == "etf" and verdict == "UNKNOWN" and tech.rsi_14 is not None:
            if tech.trend == "uptrend" and tech.rsi_14 < 70:
                verdict, label = "BUY", "Comprar (momentum)"
            elif tech.trend == "downtrend" and tech.rsi_14 > 30:
                verdict, label = "SELL", "Evitar (tendência ruim)"
            elif tech.rsi_14 <= 30:
                verdict, label = "BUY", "Comprar (sobrevendido)"
            elif tech.rsi_14 >= 70:
                verdict, label = "HOLD", "Aguardar (sobrecomprado)"
            else:
                verdict, label = "HOLD", "Manter"

        return Opportunity(
            ticker=record.ticker,
            name=record.name,
            asset_type=AssetType(record.asset_type),
            sector=record.sector,
            price=record.price,
            fair_price=fair.consensus,
            bazin=fair.bazin,
            graham=fair.graham,
            pvp=fair.pvp,
            margin_of_safety=fair.margin_of_safety,
            dividend_yield=record.dividend_yield,
            verdict=verdict,
            label=label,
            confidence=dec.confidence,
            data_years=fair.data_years,
            consensus_methods=fair.consensus_methods,
            trend_basis=tech.trend_basis,
            category_resolved=auto_category(
                record.asset_type, record.dividend_yield, record.has_dividend_history
            ),
            score=score,
            score_breakdown=breakdown,
            data_completeness=breakdown.get("data_completeness", 1.0),
            reasons=dec.reasons,
        )

    @staticmethod
    def _decode(cached: dict) -> tuple[list[_MarketRecord], int]:
        return (
            [_MarketRecord.from_dict(r) for r in cached["items"]],
            cached["universe_size"],
        )

    async def _scan_market(self) -> tuple[list[_MarketRecord], int]:
        """Dado de mercado do universo, com stale-while-revalidate.

        Fresco: devolve na hora. Vencido mas ainda utilizável: devolve o antigo
        e dispara o recálculo em background. Sem nada em cache: aí sim paga o
        scan (primeiro acesso após um deploy, ou cache limpo).
        """
        cached, stale_by = cache.get_with_age(_SCAN_CACHE_KEY)

        if cached is not None and stale_by == 0:
            return self._decode(cached)

        if cached is not None and stale_by is not None and stale_by <= _SCAN_STALE_TOLERANCE:
            await self._schedule_refresh()
            logger.info("Servindo scan vencido há %.0f s enquanto recalcula.", stale_by)
            return self._decode(cached)

        return await self._refresh_market()

    async def _schedule_refresh(self) -> None:
        """Garante no máximo um recálculo em background por vez."""
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
            # revalida: outra request pode ter preenchido o cache enquanto esperávamos o lock
            cached, stale_by = cache.get_with_age(_SCAN_CACHE_KEY)
            if cached is not None and stale_by == 0:
                return self._decode(cached)

            universe = sorted(set(await asyncio.to_thread(get_universe)))
            universe_size = len(universe)
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
        """Oportunidades já personalizadas para `prefs`."""
        records, universe_size = await self._scan_market()
        return [self._build_opportunity(r, prefs) for r in records], universe_size

    async def scan_for_current_user(self) -> tuple[list[Opportunity], int]:
        """Scan personalizado, memoizado por request.

        /dashboard, /strategy e /rebalance-suggestions passam por aqui; a tela
        de Estratégia chamava duas rotas que rodavam o pipeline cada uma.
        """

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
    ) -> OpportunitiesResponse:
        prefs = self.portfolio_repo.get_preferences()

        held = {p["ticker"].upper() for p in self.portfolio_repo.list_positions()}

        scanned, universe_size = await self.scan_for_current_user()
        scanned_count = len(scanned)
        # Copia: os filtros e o boost por preferência mutam `score`, e o
        # resultado memoizado é compartilhado com as outras rotas do request.
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

        return OpportunitiesResponse(
            items=paginated_list,
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
            universe_size=universe_size,
            failed_count=universe_size - scanned_count,
        )
