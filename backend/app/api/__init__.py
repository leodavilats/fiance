from fastapi import APIRouter, Depends

from app.core.auth import get_current_user, require_admin
from app.core.ratelimit import rate_limit

from . import (
    account,
    alerts,
    assets,
    auth,
    basic,
    benchmark,
    billing,
    dashboard,
    data_quality,
    demo,
    dip_scanner,
    dividends,
    entitlements,
    events,
    fixed_income,
    followed,
    goals,
    income_compare,
    notifications,
    onboarding,
    opportunities,
    portfolio_routes,
    preferences,
    projection,
    public,
    quick_invest,
    referral,
    renda_fixa,
    search,
    sectors,
    strategy,
    transactions,
    whats_new,
)

router = APIRouter()

router.include_router(basic.router, tags=["Basic"])
router.include_router(auth.router, tags=["Auth"])
router.include_router(public.router, tags=["Público"])
router.include_router(billing.public_router, tags=["Cobrança"])

protected = APIRouter(dependencies=[Depends(get_current_user), Depends(rate_limit)])
protected.include_router(
    basic.admin_router, tags=["Maintenance"], dependencies=[Depends(require_admin)]
)
protected.include_router(
    events.admin_router, tags=["Analytics"], dependencies=[Depends(require_admin)]
)
protected.include_router(data_quality.router, tags=["Maintenance"])
protected.include_router(account.router, tags=["Account"])
protected.include_router(entitlements.router, tags=["Entitlement"])
protected.include_router(billing.router, tags=["Cobrança"])
protected.include_router(referral.router, tags=["Indicação"])
protected.include_router(search.router, tags=["Busca"])
protected.include_router(
    billing.admin_router, tags=["Cobrança"], dependencies=[Depends(require_admin)]
)
protected.include_router(events.router, tags=["Analytics"])
protected.include_router(assets.router, tags=["Assets"])
protected.include_router(dip_scanner.router, tags=["Dip Scanner"])
protected.include_router(portfolio_routes.router, tags=["Portfolio"])
protected.include_router(transactions.router, tags=["Livro-razão"])
protected.include_router(goals.router, tags=["Goals"])
protected.include_router(onboarding.router, tags=["Onboarding"])
protected.include_router(demo.router, tags=["Onboarding"])
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
