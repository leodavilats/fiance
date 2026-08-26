import asyncio
import time

from app.analysis.classify import auto_category, resolve_category
from app.analysis.decision import decide
from app.analysis.fair_price import compute_fair_price, compute_technical, desired_yield_for
from app.core.context import memoize_request
from app.core.errors import DomainError, NotFoundError
from app.models import (
    AssetType,
    ClosedTrade,
    ClosedTradesResponse,
    PortfolioEvaluationRequest,
    PortfolioEvaluationResponse,
    PortfolioItem,
    PortfolioPosition,
    PortfolioSnapshot,
    PortfolioStateResponse,
    SavePortfolioRequest,
    SellRequest,
    StoredPortfolioItem,
    TaxLossCategoryBalance,
)
from app.optimizer.cost_calculator import calculate_sell_cost
from app.repositories import AssetRepository, PortfolioRepository

_SOLD_AT_CLOCK_SKEW_SECONDS = 5 * 60
_SOLD_AT_MAX_BACKDATE_SECONDS = 90 * 24 * 3600


class PortfolioService:
    def __init__(self):
        self.asset_repo = AssetRepository()
        self.portfolio_repo = PortfolioRepository()

    async def evaluate_portfolio(
        self, req: PortfolioEvaluationRequest
    ) -> PortfolioEvaluationResponse:
        if not req.items:
            raise DomainError("Carteira vazia.")

        prefs = self.portfolio_repo.get_preferences()

        async def _one(item: PortfolioItem) -> PortfolioPosition:

            try:
                snap = await self.asset_repo.get_asset(item.ticker)
            except Exception:
                snap = None

            if not snap:
                return PortfolioPosition(
                    ticker=item.ticker.upper(),
                    name=None,
                    asset_type=AssetType.br_stock,
                    quantity=item.quantity,
                    avg_price=item.avg_price,
                    current_price=None,
                    invested=round(item.quantity * item.avg_price, 2),
                    current_value=None,
                    pnl=None,
                    pnl_pct=None,
                    fair_price=None,
                    margin_of_safety=None,
                    verdict="UNKNOWN",
                    label="Sem dados",
                    reasons=[f"Não conseguimos coletar dados de {item.ticker}."],
                    category=item.category,
                    category_resolved=resolve_category(item.category, "acoes_br"),
                )

            history, dividends = await asyncio.gather(
                self.asset_repo.get_history(item.ticker, period="2y"),
                self.asset_repo.get_dividends(item.ticker),
            )

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
            dec = decide(fair, tech, current_price=snap.price, avg_cost=item.avg_price)

            invested = item.quantity * item.avg_price
            current = (snap.price or 0) * item.quantity if snap.price else None
            pnl = (current - invested) if current is not None else None
            pnl_pct = (pnl / invested * 100) if (pnl is not None and invested > 0) else None

            auto = auto_category(snap.asset_type, snap.dividend_yield, bool(dividends))

            return PortfolioPosition(
                ticker=snap.symbol,
                name=snap.name,
                asset_type=AssetType(snap.asset_type),
                quantity=item.quantity,
                avg_price=round(item.avg_price, 4),
                current_price=round(snap.price, 4) if snap.price else None,
                invested=round(invested, 2),
                current_value=round(current, 2) if current is not None else None,
                pnl=round(pnl, 2) if pnl is not None else None,
                pnl_pct=round(pnl_pct, 2) if pnl_pct is not None else None,
                fair_price=fair.consensus,
                margin_of_safety=fair.margin_of_safety,
                verdict=dec.verdict,
                label=dec.label,
                confidence=dec.confidence,
                data_years=fair.data_years,
                consensus_methods=fair.consensus_methods,
                trend_basis=tech.trend_basis,
                as_of=snap.as_of or None,
                reasons=dec.reasons,
                category=item.category,
                category_resolved=resolve_category(item.category, auto),
                dividend_yield=snap.dividend_yield,
                sector=snap.sector,
            )

        positions = [p for p in await asyncio.gather(*[_one(i) for i in req.items]) if p]

        total_inv = sum(p.invested for p in positions)
        total_cur = sum(p.current_value or p.invested for p in positions)
        total_pnl = total_cur - total_inv
        total_pnl_pct = (total_pnl / total_inv * 100) if total_inv > 0 else 0.0

        return PortfolioEvaluationResponse(
            positions=positions,
            total_invested=round(total_inv, 2),
            total_current=round(total_cur, 2),
            total_pnl=round(total_pnl, 2),
            total_pnl_pct=round(total_pnl_pct, 2),
        )

    async def evaluate_stored_for_current_user(self) -> PortfolioEvaluationResponse:
        """Avalia a carteira salva, memoizado por request."""

        async def _build() -> PortfolioEvaluationResponse:
            stored = self.portfolio_repo.list_positions()
            if not stored:
                return PortfolioEvaluationResponse(
                    positions=[],
                    total_invested=0.0,
                    total_current=0.0,
                    total_pnl=0.0,
                    total_pnl_pct=0.0,
                )

            return await self.evaluate_portfolio(
                PortfolioEvaluationRequest(
                    items=[
                        PortfolioItem(
                            ticker=i["ticker"],
                            quantity=i["quantity"],
                            avg_price=i["avg_price"],
                            category=i.get("category", "auto"),
                        )
                        for i in stored
                    ]
                )
            )

        return await memoize_request("portfolio.evaluate_stored", _build)

    def get_portfolio(self) -> PortfolioStateResponse:
        items = self.portfolio_repo.list_positions()
        snaps = self.portfolio_repo.list_snapshots(limit=90)

        return PortfolioStateResponse(
            items=[StoredPortfolioItem(**i) for i in items],
            last_updated=self.portfolio_repo.last_updated(),
            snapshots=[PortfolioSnapshot(**s) for s in snaps],
        )

    def upsert_position(self, item: PortfolioItem) -> PortfolioStateResponse:
        """Cria ou atualiza uma posição, sem tocar nas outras."""
        self.portfolio_repo.upsert_position(
            ticker=item.ticker,
            quantity=item.quantity,
            avg_price=item.avg_price,
            category=item.category or "auto",
        )
        return self.get_portfolio()

    def save_portfolio(self, req: SavePortfolioRequest) -> PortfolioStateResponse:
        self.portfolio_repo.replace_all(
            [
                {
                    "ticker": i.ticker,
                    "quantity": i.quantity,
                    "avg_price": i.avg_price,
                    "category": i.category or "auto",
                }
                for i in req.items
            ]
        )

        items = self.portfolio_repo.list_positions()
        snaps = self.portfolio_repo.list_snapshots(limit=90)

        return PortfolioStateResponse(
            items=[StoredPortfolioItem(**i) for i in items],
            last_updated=self.portfolio_repo.last_updated(),
            snapshots=[PortfolioSnapshot(**s) for s in snaps],
        )

    def delete_position(self, ticker: str) -> dict:
        self.portfolio_repo.delete_position(ticker)
        return {"deleted": ticker.upper()}

    async def sell_position(self, req: SellRequest) -> ClosedTrade:
        pos = self.portfolio_repo.get_position(req.ticker)
        if pos is None:
            raise NotFoundError(f"Posição {req.ticker.upper()} não encontrada na carteira.")
        if req.quantity > pos["quantity"] + 1e-9:
            raise DomainError(
                f"Quantidade de venda ({req.quantity}) maior que a quantidade em carteira "
                f"({pos['quantity']})."
            )

        try:
            snap = await self.asset_repo.get_asset(req.ticker)
            asset_type = snap.asset_type if snap else None
        except Exception:
            asset_type = None

        auto = auto_category(asset_type) if asset_type else "acoes_br"
        category = resolve_category(pos["category"], auto)

        sold_at = self._validate_sold_at(req.sold_at)

        self.portfolio_repo.lock_tenant()

        month_before = self.portfolio_repo.sum_gross_sales_in_month(category, at=sold_at)

        accumulated_loss = self.portfolio_repo.available_tax_loss(category)

        cost = calculate_sell_cost(
            category,
            req.quantity,
            req.sell_price,
            pos["avg_price"],
            gross_value_month_before=month_before,
            accumulated_loss=accumulated_loss,
        )

        trade = self.portfolio_repo.create_closed_trade(
            ticker=req.ticker.upper(),
            category=category,
            quantity=req.quantity,
            avg_price=pos["avg_price"],
            sell_price=req.sell_price,
            gross_profit=cost.gross_profit,
            ir_rate=cost.ir_rate,
            ir_amount=cost.ir_amount,
            net_profit=cost.net_profit,
            loss_offset_used=cost.loss_offset_used,
            taxable_profit=cost.taxable_profit,
            loss_compensable=cost.loss_compensable,
            sold_at=sold_at,
        )
        self.portfolio_repo.reduce_position_quantity(req.ticker, req.quantity)
        return ClosedTrade(**trade)

    @staticmethod
    def _validate_sold_at(sold_at: float | None) -> float:
        """Data de venda controlada pelo cliente, com janela fechada."""
        now = time.time()
        if sold_at is None:
            return now

        if sold_at > now + _SOLD_AT_CLOCK_SKEW_SECONDS:
            raise DomainError("A data da venda não pode estar no futuro.")
        if sold_at < now - _SOLD_AT_MAX_BACKDATE_SECONDS:
            raise DomainError(
                "A data da venda não pode ser anterior a 90 dias — a isenção mensal de "
                "IR e a alíquota dependem do mês da operação."
            )
        return sold_at

    def get_closed_trades(self) -> ClosedTradesResponse:
        trades = self.portfolio_repo.list_closed_trades()
        total_realized = sum(t["net_profit"] for t in trades)
        total_ir = sum(t["ir_amount"] for t in trades)
        balances = self.portfolio_repo.tax_loss_balances()

        return ClosedTradesResponse(
            trades=[ClosedTrade(**t) for t in trades],
            total_realized_pnl=round(total_realized, 2),
            total_ir_paid=round(total_ir, 2),
            tax_loss_balances=[TaxLossCategoryBalance(**b) for b in balances],
            total_tax_loss_available=round(sum(b["available"] for b in balances), 2),
        )
