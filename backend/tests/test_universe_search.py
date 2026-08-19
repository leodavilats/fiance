from app.core import universe


def _fake_stocks():
    return [
        {"stock": "PETR4", "name": "Petrobras PN", "sector": "Energy"},
        {"stock": "PETR3", "name": "Petrobras ON", "sector": "Energy"},
        {"stock": "VALE3", "name": "Vale ON", "sector": "Basic Materials"},
        {"stock": "ITUB4", "name": "Itau Unibanco PN", "sector": "Finance"},
        {"stock": "PETR4F", "name": "Petrobras PN (fracionário)", "sector": "Energy"},
    ]


def test_search_by_ticker_prefix(monkeypatch):
    monkeypatch.setattr(universe, "_get_brapi_stocks_cached", _fake_stocks)
    results = universe.search_universe("PETR")
    tickers = [r["ticker"] for r in results]
    assert "PETR4" in tickers
    assert "PETR3" in tickers
    # Lotes fracionários não devem aparecer no autocomplete.
    assert "PETR4F" not in tickers


def test_search_by_company_name(monkeypatch):
    monkeypatch.setattr(universe, "_get_brapi_stocks_cached", _fake_stocks)
    results = universe.search_universe("itau")
    assert any(r["ticker"] == "ITUB4" for r in results)


def test_search_empty_query_returns_nothing(monkeypatch):
    monkeypatch.setattr(universe, "_get_brapi_stocks_cached", _fake_stocks)
    assert universe.search_universe("") == []


def test_search_prioritizes_prefix_match(monkeypatch):
    monkeypatch.setattr(universe, "_get_brapi_stocks_cached", _fake_stocks)
    results = universe.search_universe("PETR")
    # PETR3/PETR4 começam com a busca — devem vir antes de qualquer match
    # que só contenha "PETR" no meio do nome/ticker.
    assert results[0]["ticker"].startswith("PETR")


def test_search_does_not_return_unsupported_tickers(monkeypatch):
    monkeypatch.setattr(universe, "_get_brapi_stocks_cached", list)
    results = universe.search_universe("bitcoin")
    assert results == []

    results = universe.search_universe("AAPL")
    assert results == []


def test_search_respects_limit(monkeypatch):
    many_stocks = [
        {"stock": f"TST{i}", "name": f"Teste {i}", "sector": "Finance"} for i in range(20)
    ]
    monkeypatch.setattr(universe, "_get_brapi_stocks_cached", lambda: many_stocks)
    results = universe.search_universe("TST", limit=5)
    assert len(results) == 5
