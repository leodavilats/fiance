from datetime import datetime, timedelta

from app.models.projection import (
    PassiveIncomeMonth,
    PassiveIncomeProjectionRequest,
    PassiveIncomeProjectionResponse,
    SectorAllocation,
    SectorAllocationResponse,
)
from app.repositories import AssetRepository, PortfolioRepository


class ProjectionService:
    def __init__(self):
        self.portfolio_repo = PortfolioRepository()
        self.asset_repo = AssetRepository()

    async def project_passive_income(
        self, req: PassiveIncomeProjectionRequest
    ) -> PassiveIncomeProjectionResponse:

        stored = self.portfolio_repo.list_positions()

        current_value = 0.0
        current_dividends_yearly = 0.0

        for item in stored:
            snap = await self.asset_repo.get_asset(item.ticker)
            if not snap or not snap.price:
                continue

            position_value = item.quantity * snap.price
            current_value += position_value

            if snap.dividend_yield:
                position_dividends = position_value * (snap.dividend_yield / 100)
                current_dividends_yearly += position_dividends

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

    async def analyze_sector_allocation(
        self, target_allocations: dict[str, float]
    ) -> SectorAllocationResponse:

        stored = self.portfolio_repo.list_positions()

        sector_values: dict[str, float] = {}
        total_equity_value = 0.0

        for item in stored:
            snap = await self.asset_repo.get_asset(item.ticker)
            if not snap or not snap.price:
                continue

            if snap.asset_type not in ["br_stock", "us_stock", "bdr"]:
                continue

            position_value = item.quantity * snap.price
            total_equity_value += position_value

            sector = snap.sector or "Outros"
            sector_values[sector] = sector_values.get(sector, 0) + position_value

        allocations: list[SectorAllocation] = []
        max_deviation = 0.0
        needs_rebalance = False

        for sector, target_pct in target_allocations.items():
            current_value = sector_values.get(sector, 0.0)
            current_pct = (
                (current_value / total_equity_value * 100) if total_equity_value > 0 else 0
            )
            deviation = current_pct - target_pct

            allocations.append(
                SectorAllocation(
                    sector=sector,
                    target_percentage=target_pct,
                    current_percentage=round(current_pct, 2),
                    current_value=round(current_value, 2),
                    deviation=round(deviation, 2),
                )
            )

            if abs(deviation) > max_deviation:
                max_deviation = abs(deviation)

            if abs(deviation) >= 5:
                needs_rebalance = True

        for sector, value in sector_values.items():
            if sector not in target_allocations:
                current_pct = (value / total_equity_value * 100) if total_equity_value > 0 else 0
                allocations.append(
                    SectorAllocation(
                        sector=sector,
                        target_percentage=0.0,
                        current_percentage=round(current_pct, 2),
                        current_value=round(value, 2),
                        deviation=round(current_pct, 2),
                    )
                )
                needs_rebalance = True

        return SectorAllocationResponse(
            total_equity_value=round(total_equity_value, 2),
            allocations=allocations,
            needs_rebalance=needs_rebalance,
            max_deviation=round(max_deviation, 2),
        )
