from app.analysis.fair_price import (
    FairPriceInputs,
    FairPriceResult,
    ValuationRates,
    compute_fair_price_inputs,
    desired_yield_for,
    fair_price_from_inputs,
    rates_for_valuation,
)
from app.collectors import rates as rates_source


def valuation_rates() -> ValuationRates | None:
    return rates_for_valuation(rates_source.get_rates())


def fair_price_inputs_for(snap, dividends: list[dict] | None) -> FairPriceInputs:
    return compute_fair_price_inputs(
        price=snap.price,
        eps=snap.eps,
        book_value=snap.book_value,
        dividends=dividends,
        asset_type=str(snap.asset_type),
        pb_ratio=snap.pb_ratio,
        roe_pct=snap.roe,
        net_income_history=getattr(snap, "net_income_history", None),
        equity_history=getattr(snap, "equity_history", None),
        net_income_ttm=getattr(snap, "net_income_ttm", None),
        rates=valuation_rates(),
        symbol=snap.symbol,
    )


def fair_price_for(snap, dividends: list[dict] | None, prefs: dict | None) -> FairPriceResult:
    return fair_price_from_inputs(
        fair_price_inputs_for(snap, dividends),
        desired_yield=desired_yield_for(str(snap.asset_type), prefs),
    )
