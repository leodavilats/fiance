from app.analysis.portfolio_health import compute_portfolio_health
from app.models import AssetType, CategoryAllocation, PortfolioPosition


def _position(
    ticker,
    value,
    verdict="HOLD",
    sector=None,
    category_resolved="acoes_br",
) -> PortfolioPosition:
    return PortfolioPosition(
        ticker=ticker,
        name=ticker,
        asset_type=AssetType.br_stock,
        quantity=1,
        avg_price=value,
        current_price=value,
        invested=value,
        current_value=value,
        pnl=0,
        pnl_pct=0,
        fair_price=value,
        margin_of_safety=0,
        verdict=verdict,
        label=verdict,
        sector=sector,
        category_resolved=category_resolved,
    )


def _allocation(category, current_value, target_pct=20.0) -> CategoryAllocation:
    return CategoryAllocation(
        category=category,
        current_value=current_value,
        current_pct=0,
        target_pct=target_pct,
    )


def test_no_positions_returns_none():
    assert compute_portfolio_health([], []) is None


def test_diversified_low_risk_portfolio_scores_well():
    positions = [
        _position("PETR4", 1000, sector="Energia"),
        _position("VALE3", 1000, sector="Mineração"),
        _position("ITUB4", 1000, sector="Financeiro"),
        _position("WEGE3", 1000, sector="Industrial"),
    ]
    allocations = [
        _allocation("acoes_br", 4000),
        _allocation("fiis", 1000),
        _allocation("renda_fixa", 1000),
    ]

    health = compute_portfolio_health(positions, allocations)

    assert health is not None
    assert health.score > 60
    assert health.warnings == []


def test_concentrated_single_asset_flags_warning():
    positions = [
        _position("PETR4", 9000, sector="Energia"),
        _position("VALE3", 1000, sector="Mineração"),
    ]
    allocations = [_allocation("acoes_br", 10000)]

    health = compute_portfolio_health(positions, allocations)

    assert health is not None
    assert health.top_position_ticker == "PETR4"
    assert health.top_position_pct == 90.0
    assert any("PETR4" in w for w in health.warnings)
    assert health.concentration_score < 30


def test_sell_signal_positions_reduce_risk_score():
    positions = [
        _position("PETR4", 5000, verdict="STRONG_SELL", sector="Energia"),
        _position("VALE3", 5000, sector="Mineração"),
    ]
    allocations = [_allocation("acoes_br", 10000)]

    health = compute_portfolio_health(positions, allocations)

    assert health is not None
    assert health.risk_score < 100
    assert any("sinal de venda" in w for w in health.warnings)
