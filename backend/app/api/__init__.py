# flake8: noqa

from fastapi import APIRouter

from . import (
    assets,
    basic,
    dashboard,
    dip_scanner,
    goals,
    opportunities,
    portfolio_routes,
    preferences,
    recommendations,
    renda_fixa,
    strategy,
    watchlist,
)

# Create main router
router = APIRouter()

# Register all routers
router.include_router(basic.router, tags=["Basic"])
router.include_router(recommendations.router, tags=["Recommendations"])
router.include_router(assets.router, tags=["Assets"])
router.include_router(dip_scanner.router, tags=["Dip Scanner"])
router.include_router(portfolio_routes.router, tags=["Portfolio"])
router.include_router(watchlist.router, tags=["Watchlist"])
router.include_router(goals.router, tags=["Goals"])
router.include_router(preferences.router, tags=["Preferences"])
router.include_router(opportunities.router, tags=["Opportunities"])
router.include_router(dashboard.router, tags=["Dashboard"])
router.include_router(strategy.router, tags=["Strategy"])
router.include_router(renda_fixa.router, tags=["Renda Fixa"])

__all__ = ["router"]
