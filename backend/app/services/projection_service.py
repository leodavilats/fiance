import asyncio
from datetime import datetime, timedelta

from app.analysis.scenarios import (
    DISCLAIMER,
    OPTIMISTIC_FACTOR,
    SCENARIOS,
    Scenario,
    band,
)
from app.models.projection import (
    PassiveIncomeMonth,
    PassiveIncomeProjectionRequest,
    PassiveIncomeProjectionResponse,
    ScenarioMonth,
    ScenarioSeries,
    TargetEstimate,
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
        base_date = datetime.now()

        def _mes(indice: int) -> str:
            return (base_date + timedelta(days=30 * (indice + 1))).strftime("%Y-%m")

        def _rodar(cenario: Scenario) -> ScenarioSeries:
            """Roda a projeção inteira sob um conjunto de premissas.

            É a mesma conta de sempre, parametrizada. Duplicar o laço por
            cenário seria a maneira mais fácil de os três divergirem em silêncio
            depois da primeira manutenção.
            """
            valorizacao_ano, dividendos_ano = cenario.rates(
                req.portfolio_growth_rate, req.dividend_growth_rate
            )
            portfolio_growth = valorizacao_ano / 12
            div_growth = dividendos_ano / 12

            portfolio_val = current_value
            yearly_dividends = current_dividends_yearly
            meses: list[ScenarioMonth] = []
            meses_ate_meta = None
            data_meta = None

            for month_idx in range(months):
                portfolio_val *= 1 + portfolio_growth
                portfolio_val += monthly_contrib
                yearly_dividends *= 1 + div_growth

                if req.reinvest_dividends:
                    portfolio_val += yearly_dividends / 12
                    yearly_dividends = portfolio_val * (current_dy_avg / 100)

                renda_mensal = yearly_dividends / 12
                meses.append(
                    ScenarioMonth(
                        scenario=cenario.code,
                        month=_mes(month_idx),
                        portfolio_value=round(portfolio_val, 2),
                        passive_income_monthly=round(renda_mensal, 2),
                    )
                )

                if req.target_monthly_income and meses_ate_meta is None:
                    if renda_mensal >= req.target_monthly_income:
                        meses_ate_meta = month_idx + 1
                        data_meta = meses[-1].month

            return ScenarioSeries(
                code=cenario.code,
                label=cenario.label,
                rationale=cenario.rationale,
                portfolio_growth_rate=valorizacao_ano,
                dividend_growth_rate=dividendos_ano,
                months=meses,
                final_passive_income_monthly=meses[-1].passive_income_monthly if meses else 0.0,
                final_portfolio_value=meses[-1].portfolio_value if meses else current_value,
                months_to_target=meses_ate_meta,
                target_date=data_meta,
            )

        series = {cenario.code: _rodar(cenario) for cenario in SCENARIOS}
        base = series["base"]

        projections: list[PassiveIncomeMonth] = []
        for idx, mes_base in enumerate(base.months):
            piso_valor, teto_valor = band([s.months[idx].portfolio_value for s in series.values()])
            piso_renda, teto_renda = band(
                [s.months[idx].passive_income_monthly for s in series.values()]
            )
            projections.append(
                PassiveIncomeMonth(
                    month=mes_base.month,
                    portfolio_value=mes_base.portfolio_value,
                    portfolio_value_low=round(piso_valor, 2),
                    portfolio_value_high=round(teto_valor, 2),
                    passive_income_monthly=mes_base.passive_income_monthly,
                    passive_income_monthly_low=round(piso_renda, 2),
                    passive_income_monthly_high=round(teto_renda, 2),
                    passive_income_yearly=round(mes_base.passive_income_monthly * 12, 2),
                    dividend_yield_avg=round(current_dy_avg, 2),
                )
            )

        alvo = None
        if req.target_monthly_income:
            otimista = series["otimista"]
            conservador = series["conservador"]
            alvo = TargetEstimate(
                monthly_income=req.target_monthly_income,
                earliest_months=otimista.months_to_target,
                expected_months=base.months_to_target,
                latest_months=conservador.months_to_target,
                earliest_date=otimista.target_date,
                expected_date=base.target_date,
                latest_date=conservador.target_date,
                # Um cenário que não chega no horizonte é resposta, não falha.
                # Esconder isso faria a meta parecer garantida.
                reached_in_all_scenarios=all(
                    s.months_to_target is not None for s in series.values()
                ),
            )

        return PassiveIncomeProjectionResponse(
            current_passive_income_monthly=round(current_monthly_income, 2),
            current_passive_income_yearly=round(current_dividends_yearly, 2),
            current_portfolio_value=round(current_value, 2),
            current_dividend_yield_avg=round(current_dy_avg, 2),
            projections=projections,
            scenarios=[series[c.code] for c in SCENARIOS],
            target=alvo,
            target_monthly_income=req.target_monthly_income,
            disclaimer=DISCLAIMER,
            assumptions={
                "monthly_contribution": monthly_contrib,
                "dividend_growth_rate_yearly": req.dividend_growth_rate,
                "portfolio_growth_rate_yearly": req.portfolio_growth_rate,
                "reinvest_dividends": req.reinvest_dividends,
                "scenario_spread": (
                    "Conservador zera o crescimento; otimista multiplica as premissas "
                    f"por {OPTIMISTIC_FACTOR:.1f}. A largura da faixa é escolhida, "
                    "não estimada."
                ),
            },
        )
