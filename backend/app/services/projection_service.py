import asyncio
from datetime import datetime, timedelta

from app.models.projection import (
    PassiveIncomeMonth,
    PassiveIncomeProjectionRequest,
    PassiveIncomeProjectionResponse,
)
from app.repositories import AssetRepository, PortfolioRepository
from app.services.fixed_income_service import FixedIncomeService


class ProjectionService:
    def __init__(self):
        self.portfolio_repo = PortfolioRepository()
        self.asset_repo = AssetRepository()
        self.fixed_income = FixedIncomeService()

    async def project_passive_income(
        self, req: PassiveIncomeProjectionRequest
    ) -> PassiveIncomeProjectionResponse:

        stored = self.portfolio_repo.list_positions()

        current_value = 0.0
        current_dividends_yearly = 0.0

        # list_positions() devolve dicts (TypedDict). O acesso por atributo
        # (`item.ticker`) levantava AttributeError, capturado pelo except logo
        # abaixo e transformado em `continue` — o endpoint reportava, em
        # silêncio, patrimônio atual R$ 0 e renda atual R$ 0 para todo mundo.
        async def _snapshot(ticker: str):
            try:
                return await self.asset_repo.get_asset(ticker)
            except Exception:
                return None

        snaps = await asyncio.gather(*[_snapshot(item["ticker"]) for item in stored])

        for item, snap in zip(stored, snaps, strict=True):
            if not snap or not snap.price:
                continue

            position_value = item["quantity"] * snap.price
            current_value += position_value

            if snap.dividend_yield:
                current_dividends_yearly += position_value * (snap.dividend_yield / 100)

        # A projeção ignorava 100% da renda fixa: um investidor conservador via
        # a renda futura projetada só sobre o aporte mensal.
        for rf in self.fixed_income.as_portfolio_positions():
            rf_value = rf.current_value or rf.invested
            current_value += rf_value
            if rf.dividend_yield:
                current_dividends_yearly += rf_value * (rf.dividend_yield / 100)

        current_dy_avg = (
            (current_dividends_yearly / current_value * 100) if current_value > 0 else 0
        )
        current_monthly_income = current_dividends_yearly / 12

        months = req.months_ahead
        monthly_contrib = req.monthly_contribution
        div_growth = req.dividend_growth_rate / 12
        portfolio_growth = req.portfolio_growth_rate / 12
        reinvest = req.reinvest_dividends

        projections: list[PassiveIncomeMonth] = []
        portfolio_val = current_value
        yearly_dividends = current_dividends_yearly

        base_date = datetime.now()
        months_to_target = None
        target_date = None

        for month_idx in range(months):
            portfolio_val *= 1 + portfolio_growth

            portfolio_val += monthly_contrib

            yearly_dividends *= 1 + div_growth

            if reinvest:
                monthly_div = yearly_dividends / 12
                portfolio_val += monthly_div

                yearly_dividends = portfolio_val * (current_dy_avg / 100)

            proj_date = base_date + timedelta(days=30 * (month_idx + 1))
            month_str = proj_date.strftime("%Y-%m")

            monthly_income = yearly_dividends / 12
            projections.append(
                PassiveIncomeMonth(
                    month=month_str,
                    portfolio_value=round(portfolio_val, 2),
                    passive_income_monthly=round(monthly_income, 2),
                    passive_income_yearly=round(yearly_dividends, 2),
                    dividend_yield_avg=round(current_dy_avg, 2),
                )
            )

            if req.target_monthly_income and months_to_target is None:
                if monthly_income >= req.target_monthly_income:
                    months_to_target = month_idx + 1
                    target_date = month_str

        return PassiveIncomeProjectionResponse(
            current_passive_income_monthly=round(current_monthly_income, 2),
            current_passive_income_yearly=round(current_dividends_yearly, 2),
            current_portfolio_value=round(current_value, 2),
            current_dividend_yield_avg=round(current_dy_avg, 2),
            projections=projections,
            target_monthly_income=req.target_monthly_income,
            months_to_target=months_to_target,
            target_date=target_date,
            assumptions={
                "monthly_contribution": monthly_contrib,
                "dividend_growth_rate_yearly": req.dividend_growth_rate,
                "portfolio_growth_rate_yearly": req.portfolio_growth_rate,
                "reinvest_dividends": reinvest,
            },
        )
