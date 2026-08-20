from __future__ import annotations

from app.analysis.renda_fixa_analysis import analyze_one
from app.collectors.rates import get_rates
from app.models.enums import Liquidez, RendaFixaType, TaxType
from app.models.income_compare import IncomeCompareResponse, IncomeOption
from app.models.renda_fixa import RendaFixaAsset
from app.services.fixed_income_service import FixedIncomeService
from app.services.opportunity_service import OpportunityService

MAX_ASSETS = 8

# Ofertas de referência do mercado, para o comparativo existir mesmo antes de o
# usuário cadastrar qualquer aplicação.
_REFERENCE_OFFERS = [
    ("CDB 100% do CDI (liquidez diária)", 100.0, RendaFixaType.cdb, Liquidez.diaria),
    ("CDB 110% do CDI (no vencimento)", 110.0, RendaFixaType.cdb, Liquidez.no_vencimento),
    ("LCI 90% do CDI (isenta de IR)", 90.0, RendaFixaType.lci, Liquidez.no_vencimento),
]

# FII distribui rendimento isento para pessoa física; dividendo de ação também
# é isento hoje. Por isso o DY é comparável direto com a taxa **líquida** da
# renda fixa, sem novo desconto.
_EXEMPT_INCOME_TYPES = {"fii", "br_stock"}


class IncomeCompareService:
    def __init__(self):
        self.fixed_income = FixedIncomeService()
        self.opportunities = OpportunityService()

    async def compare(self, amount: float, horizon_months: int) -> IncomeCompareResponse:
        rates = get_rates()

        fixed_income = self._fixed_income_options(amount, horizon_months, rates)
        assets = await self._asset_options(amount)

        pool = fixed_income + assets
        best = max(pool, key=lambda o: o.net_income_yield_pct) if pool else None

        return IncomeCompareResponse(
            amount=round(amount, 2),
            horizon_months=horizon_months,
            cdi_anual=rates["cdi_anual"],
            ipca_anual=rates["ipca_anual"],
            rates_source=rates["source"],
            fixed_income=fixed_income,
            assets=assets,
            best_income_option=best,
            verdict=self._verdict(fixed_income, assets, best),
        )

    # --- renda fixa ------------------------------------------------------

    def _fixed_income_options(
        self, amount: float, horizon_months: int, rates: dict
    ) -> list[IncomeOption]:
        options: list[IncomeOption] = []

        for label, pct_cdi, tipo, liquidez in _REFERENCE_OFFERS:
            result = analyze_one(
                RendaFixaAsset(
                    tipo=tipo,
                    valor_investido=amount,
                    taxa=rates["cdi_anual"],
                    prazo_meses=horizon_months,
                    tipo_taxa=TaxType.pos_fixado,
                    percentual_cdi=pct_cdi,
                    liquidez=liquidez,
                ),
                cdi_anual=rates["cdi_anual"],
                selic_anual=rates["selic_anual"],
                ipca_anual=rates["ipca_anual"],
            )
            options.append(
                IncomeOption(
                    kind="renda_fixa",
                    label=label,
                    net_income_yield_pct=result.taxa_liquida_aa,
                    income_basis=(
                        f"{pct_cdi:.0f}% do CDI ({rates['cdi_anual']:.2f}% a.a.) por "
                        f"{horizon_months} meses"
                    ),
                    has_upside=False,
                    liquidity=liquidez.value,
                    tax_note=(
                        "Isento de IR"
                        if result.isento_ir
                        else f"IR de {result.ir.aliquota_pct:.1f}% sobre o rendimento"
                    ),
                    risk_note="Risco de crédito do emissor, coberto pelo FGC até R$ 250 mil.",
                    monthly_income_estimate=round(amount * (result.taxa_liquida_aa / 100) / 12, 2),
                )
            )

        # As aplicações que o usuário já tem entram no comparativo: é o retorno
        # dele, não uma oferta hipotética.
        for position in self.fixed_income.list_positions().items:
            if position.oculto:
                continue
            options.append(
                IncomeOption(
                    kind="renda_fixa",
                    label=f"{position.nome} (sua carteira)",
                    net_income_yield_pct=round(position.yield_equivalente_pct, 2),
                    income_basis=(
                        f"taxa contratada de {position.taxa_anual_efetiva_pct:.2f}% a.a."
                    ),
                    has_upside=False,
                    liquidity=position.liquidez.value,
                    tax_note="Isento de IR"
                    if position.isento_ir
                    else "Tributado na tabela regressiva",
                    risk_note="Risco de crédito do emissor.",
                    monthly_income_estimate=round(
                        position.valor_atual * (position.yield_equivalente_pct / 100) / 12, 2
                    ),
                )
            )

        options.sort(key=lambda o: -o.net_income_yield_pct)
        return options

    # --- ativos de bolsa -------------------------------------------------

    async def _asset_options(self, amount: float) -> list[IncomeOption]:
        scanned, _universe = await self.opportunities.scan_for_current_user()

        payers = [o for o in scanned if (o.dividend_yield or 0) > 0]
        payers.sort(key=lambda o: -(o.dividend_yield or 0))

        options: list[IncomeOption] = []
        for opp in payers[:MAX_ASSETS]:
            asset_type = opp.asset_type.value
            exempt = asset_type in _EXEMPT_INCOME_TYPES

            options.append(
                IncomeOption(
                    kind=asset_type,
                    label=opp.name or opp.ticker,
                    ticker=opp.ticker,
                    net_income_yield_pct=round(opp.dividend_yield or 0, 2),
                    income_basis="dividend yield dos últimos 12 meses",
                    upside_pct=round((opp.margin_of_safety or 0) * 100, 2)
                    if opp.margin_of_safety
                    else None,
                    has_upside=True,
                    liquidity="bolsa",
                    tax_note=(
                        "Rendimento isento de IR para pessoa física"
                        if exempt
                        else "Provento tributado na fonte"
                    ),
                    risk_note=(
                        "Cotação oscila e o dividendo futuro não é garantido — "
                        "diferente da taxa contratada da renda fixa."
                    ),
                    monthly_income_estimate=round(
                        amount * ((opp.dividend_yield or 0) / 100) / 12, 2
                    ),
                    score=opp.score,
                    data_completeness=opp.data_completeness,
                )
            )

        return options

    @staticmethod
    def _verdict(
        fixed_income: list[IncomeOption],
        assets: list[IncomeOption],
        best: IncomeOption | None,
    ) -> str:
        if best is None:
            return "Sem dados suficientes para comparar agora."

        best_rf = fixed_income[0] if fixed_income else None
        best_asset = assets[0] if assets else None

        if best_rf and best_asset:
            diff = best_asset.net_income_yield_pct - best_rf.net_income_yield_pct
            if diff > 1:
                return (
                    f"{best_asset.label} paga {diff:.1f} p.p. a.a. mais de renda que a melhor "
                    f"opção de renda fixa ({best_rf.net_income_yield_pct:.2f}% a.a.) — e ainda "
                    "tem potencial de valorização. Em troca, a cotação oscila e o dividendo "
                    "não é contratado."
                )
            if diff < -1:
                return (
                    f"A renda fixa está pagando {abs(diff):.1f} p.p. a.a. mais que o melhor "
                    "pagador de dividendos da lista, com retorno contratado. Para a parte da "
                    "carteira que precisa de previsibilidade, ela vence hoje."
                )
            return (
                "Renda fixa e ativos de renda estão empatados em rendimento recorrente. "
                "A decisão passa a ser liquidez e tolerância a oscilação — não taxa."
            )

        return f"{best.label} é a melhor opção de renda disponível hoje na comparação."
