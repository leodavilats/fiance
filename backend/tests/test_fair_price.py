from app.analysis.fair_price import (
    bazin_fair_price,
    compute_fair_price,
    dcf_fair_price,
    graham_fair_price,
)


def test_bazin_fair_price_basic():
    # dividend 2/share, desired yield 10% -> fair price 20
    assert bazin_fair_price(2.0, 0.10) == 20.0


def test_bazin_fair_price_none_when_no_dividend():
    assert bazin_fair_price(None, 0.10) is None
    assert bazin_fair_price(0, 0.10) is None


def test_graham_fair_price_basic():
    # sqrt(22.5 * eps * book_value)
    assert graham_fair_price(2.0, 8.0) == 18.97


def test_graham_fair_price_none_when_missing_book_value():
    # regression: BDRs frequently have no book_value from BRAPI — must not crash
    assert graham_fair_price(2.0, None) is None


def test_graham_fair_price_none_when_negative_eps():
    assert graham_fair_price(-1.0, 8.0) is None


def test_dcf_fair_price_none_when_no_eps():
    assert dcf_fair_price(None) is None


def test_dcf_fair_price_positive_with_eps():
    result = dcf_fair_price(2.0, revenue_growth_rate=0.10)
    assert result is not None
    assert result > 0


def test_compute_fair_price_fii_never_uses_graham():
    # regression: FII fair price must consist only of bazin + P/VP, never Graham/DCF
    result = compute_fair_price(
        price=100.0,
        eps=5.0,
        book_value=90.0,
        dividends=[{"date": "2025-01-15", "value": 1.0}] * 12,
        asset_type="fii",
    )
    assert result.graham is None
    assert result.dcf is None


def test_compute_fair_price_international_never_uses_bazin():
    result = compute_fair_price(
        price=100.0,
        eps=5.0,
        book_value=20.0,
        dividends=[{"date": "2025-01-15", "value": 1.0}] * 12,
        asset_type="bdr",
    )
    assert result.bazin is None


def test_compute_fair_price_international_survives_missing_book_value():
    # regression: BDRs from BRAPI often lack book_value — Graham should
    # gracefully become None while DCF (eps-only) still computes.
    result = compute_fair_price(
        price=78.33,
        eps=2.3184,
        book_value=None,
        dividends=[],
        asset_type="bdr",
    )
    assert result.graham is None
    assert result.dcf is not None


def test_compute_fair_price_crypto_has_no_candidates():
    result = compute_fair_price(
        price=100.0,
        eps=None,
        book_value=None,
        dividends=[],
        asset_type="crypto",
    )
    assert result.consensus is None
    assert result.consensus_methods == 0
