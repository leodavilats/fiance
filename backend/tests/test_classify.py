from app.analysis.classify import auto_category, resolve_category


def test_auto_category_fii():
    assert auto_category("fii") == "fiis"


def test_auto_category_crypto():
    assert auto_category("crypto") == "cripto"


def test_auto_category_bdr_is_international():
    assert auto_category("bdr") == "acoes_int"


def test_auto_category_us_stock_is_international():
    assert auto_category("us_stock") == "acoes_int"


def test_auto_category_br_stock_default():
    assert auto_category("br_stock") == "acoes_br"


def test_resolve_category_keeps_valid_stored_value():
    assert resolve_category("fiis", "acoes_br") == "fiis"


def test_resolve_category_maps_legacy_renda_to_fiis():
    assert resolve_category("renda", "acoes_br") == "fiis"


def test_resolve_category_maps_legacy_trade_to_acoes_br():
    assert resolve_category("trade", "fiis") == "acoes_br"


def test_resolve_category_maps_legacy_caixa_to_renda_fixa():
    assert resolve_category("caixa", "fiis") == "renda_fixa"


def test_resolve_category_falls_back_to_auto_for_unknown_value():
    assert resolve_category("nonsense", "cripto") == "cripto"
