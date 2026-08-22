import pytest

from app.collectors.universal import UnsupportedTickerError, detect_type


def test_bdr_detected_before_fii_check():
    assert detect_type("AAPL34") == "bdr"
    assert detect_type("AAPL34.SA") == "bdr"


def test_known_units_are_br_stock_not_fii():
    for ticker in ["SANB11", "TAEE11", "BPAC11", "KLBN11", "SAPR11"]:
        assert detect_type(ticker) == "br_stock"


def test_unknown_ending_11_is_fii():
    assert detect_type("HGLG11") == "fii"
    assert detect_type("MXRF11") == "fii"


def test_plain_br_stock():
    assert detect_type("PETR4") == "br_stock"
    assert detect_type("VALE3") == "br_stock"


def test_known_etf_detected():
    for ticker in ["BOVA11", "IVVB11", "SMAL11"]:
        assert detect_type(ticker) == "etf"


def test_unsupported_ticker_raises():
    with pytest.raises(UnsupportedTickerError):
        detect_type("AAPL")
    with pytest.raises(UnsupportedTickerError):
        detect_type("BTC-USD")
