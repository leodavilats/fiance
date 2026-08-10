from app.collectors.universal import detect_type


def test_bdr_detected_before_fii_check():
    # AAPL34 must never be classified as br_stock/fii — regression test for the
    # bug where BDRs (ending in 3<digit>) were misdetected.
    assert detect_type("AAPL34") == "bdr"
    assert detect_type("AAPL34.SA") == "bdr"


def test_known_units_are_br_stock_not_fii():
    # Units ending in 11 that are known stocks (not FIIs) — regression test.
    for ticker in ["SANB11", "TAEE11", "BPAC11", "KLBN11", "SAPR11"]:
        assert detect_type(ticker) == "br_stock"


def test_unknown_ending_11_is_fii():
    assert detect_type("HGLG11") == "fii"
    assert detect_type("MXRF11") == "fii"


def test_plain_br_stock():
    assert detect_type("PETR4") == "br_stock"
    assert detect_type("VALE3") == "br_stock"


def test_crypto_by_suffix():
    assert detect_type("BTC-USD") == "crypto"


def test_crypto_by_known_symbol():
    assert detect_type("BTC") == "crypto"


def test_us_stock_fallback():
    assert detect_type("AAPL") == "us_stock"
    assert detect_type("MSFT") == "us_stock"
