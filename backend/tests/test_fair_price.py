from app.analysis.fair_price import (
    bazin_fair_price,
    compute_fair_price,
    dcf_fair_price,
    graham_fair_price,
)


def test_bazin_fair_price_basic():
    assert bazin_fair_price(2.0, 0.10) == 20.0


def test_bazin_fair_price_none_when_no_dividend():
    assert bazin_fair_price(None, 0.10) is None
    assert bazin_fair_price(0, 0.10) is None


def test_graham_fair_price_basic():
    assert graham_fair_price(2.0, 8.0) == 18.97


def test_graham_fair_price_none_when_missing_book_value():
    assert graham_fair_price(2.0, None) is None


def test_graham_fair_price_none_when_negative_eps():
    assert graham_fair_price(-1.0, 8.0) is None


def test_dcf_fair_price_none_when_no_eps():
    assert dcf_fair_price(None) is None


def test_dcf_fair_price_positive_with_eps():
    result = dcf_fair_price(2.0, revenue_growth_pct=10.0)
    assert result is not None
    assert result > 0


def test_dcf_uses_the_growth_it_receives_not_the_default():
    default = dcf_fair_price(2.0)
    faster = dcf_fair_price(2.0, revenue_growth_pct=20.0)
    slower = dcf_fair_price(2.0, revenue_growth_pct=2.0)

    assert faster > default > slower


def test_dcf_ignores_negative_and_absurd_growth():
    default = dcf_fair_price(2.0)
    assert dcf_fair_price(2.0, revenue_growth_pct=-15.0) == default
    assert dcf_fair_price(2.0, revenue_growth_pct=900.0) == default


def test_compute_fair_price_fii_never_uses_graham():
    result = compute_fair_price(
        price=100.0,
        eps=5.0,
        book_value=90.0,
        dividends=[{"date": "2025-01-15", "value": 1.0}] * 12,
        asset_type="fii",
    )
    assert result.graham is None
    assert result.dcf is None


def test_compute_fair_price_bdr_never_uses_bazin():
    result = compute_fair_price(
        price=100.0,
        eps=5.0,
        book_value=20.0,
        dividends=[{"date": "2025-01-15", "value": 1.0}] * 12,
        asset_type="bdr",
    )
    assert result.bazin is None


def test_compute_fair_price_bdr_survives_missing_book_value():
    result = compute_fair_price(
        price=78.33,
        eps=2.3184,
        book_value=None,
        dividends=[],
        asset_type="bdr",
    )
    assert result.graham is None
    assert result.dcf is not None


def test_compute_fair_price_etf_never_uses_graham_or_dcf():
    result = compute_fair_price(
        price=100.0,
        eps=None,
        book_value=None,
        dividends=[{"date": "2025-01-15", "value": 1.0}] * 12,
        asset_type="etf",
    )
    assert result.graham is None
    assert result.dcf is None
    assert result.bazin is not None


def test_compute_fair_price_etf_without_dividends_has_no_candidates():
    result = compute_fair_price(
        price=100.0,
        eps=None,
        book_value=None,
        dividends=[],
        asset_type="etf",
    )
    assert result.consensus is None
    assert result.consensus_methods == 0


def test_fair_price_block_keeps_consensus_methods():
    from app.models import FairPriceBlock

    fair = compute_fair_price(
        price=20.0,
        eps=2.0,
        book_value=8.0,
        dividends=[{"date": "2024-03-01", "amount": 1.0}],
        asset_type="br_stock",
    )
    block = FairPriceBlock(**fair.__dict__)

    assert block.consensus_methods == fair.consensus_methods
    assert block.consensus_methods >= 1, "ao menos um método deve entrar no consenso"
    assert block.dcf == fair.dcf


def test_technical_block_keeps_trend_basis():
    from app.analysis.fair_price import compute_technical
    from app.models import TechnicalBlock

    history = {f"2024-{1 + i // 28:02d}-{1 + i % 28:02d}": 10.0 + i * 0.1 for i in range(260)}
    tech = compute_technical(history)
    block = TechnicalBlock(**tech.__dict__)

    assert block.trend_basis == tech.trend_basis
    assert block.trend_basis in {"long", "short", "none"}
