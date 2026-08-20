from fastapi import APIRouter, Depends

from app.core.auth import get_current_user

from . import (
    alerts,
    assets,
    auth,
    basic,
    benchmark,
    dashboard,
    data_quality,
    dip_scanner,
    dividends,
    fixed_income,
    followed,
    goals,
    income_compare,
    notifications,
    opportunities,
    portfolio_routes,
    preferences,
    projection,
    quick_invest,
    renda_fixa,
    sectors,
    strategy,
    whats_new,
)

router = APIRouter()

router.include_router(basic.router, tags=["Basic"])
router.include_router(auth.router, tags=["Auth"])

protected = APIRouter(dependencies=[Depends(get_current_user)])
protected.include_router(basic.admin_router, tags=["Maintenance"])
protected.include_router(data_quality.router, tags=["Maintenance"])
protected.include_router(assets.router, tags=["Assets"])
protected.include_router(dip_scanner.router, tags=["Dip Scanner"])
protected.include_router(portfolio_routes.router, tags=["Portfolio"])
protected.include_router(goals.router, tags=["Goals"])
protected.include_router(preferences.router, tags=["Preferences"])
protected.include_router(opportunities.router, tags=["Opportunities"])
protected.include_router(dashboard.router, tags=["Dashboard"])
protected.include_router(strategy.router, tags=["Strategy"])
protected.include_router(renda_fixa.router, tags=["Renda Fixa"])
protected.include_router(fixed_income.router, tags=["Renda Fixa"])
protected.include_router(dividends.router, tags=["Dividendos"])
protected.include_router(income_compare.router, tags=["Renda Fixa"])
protected.include_router(followed.router, tags=["Sugestões"])
protected.include_router(projection.router, tags=["Projection"])
protected.include_router(quick_invest.router, tags=["Quick Invest"])
protected.include_router(benchmark.router, tags=["Benchmark"])
protected.include_router(alerts.router, tags=["Alerts"])
protected.include_router(sectors.router, tags=["Sectors"])
protected.include_router(notifications.router, tags=["Notifications"])
protected.include_router(whats_new.router, tags=["Dashboard"])

router.include_router(protected)

__all__ = ["router"]
