from app.core import universe


def _fake_stocks():
    return [
        {"codigo": "PETR4", "nome": "Petrobras PN", "setor": "Energy"},
        {"codigo": "PETR3", "nome": "Petrobras ON", "setor": "Energy"},
        {"codigo": "VALE3", "nome": "Vale ON", "setor": "Basic Materials"},
        {"codigo": "ITUB4", "nome": "Itau Unibanco PN", "setor": "Finance"},
        {"codigo": "PETR4F", "nome": "Petrobras PN (fracionário)", "setor": "Energy"},
    ]


def test_search_by_ticker_prefix(monkeypatch):
    monkeypatch.setattr(universe, "_lista", _fake_stocks)
    results = universe.search_universe("PETR")
    tickers = [r["ticker"] for r in results]
    assert "PETR4" in tickers
    assert "PETR3" in tickers
    assert "PETR4F" not in tickers


def test_search_by_company_name(monkeypatch):
    monkeypatch.setattr(universe, "_lista", _fake_stocks)
    results = universe.search_universe("itau")
    assert any(r["ticker"] == "ITUB4" for r in results)


def test_search_empty_query_returns_nothing(monkeypatch):
    monkeypatch.setattr(universe, "_lista", _fake_stocks)
    assert universe.search_universe("") == []


def test_search_prioritizes_prefix_match(monkeypatch):
    monkeypatch.setattr(universe, "_lista", _fake_stocks)
    results = universe.search_universe("PETR")
    assert results[0]["ticker"].startswith("PETR")


def test_search_does_not_return_unsupported_tickers(monkeypatch):
    monkeypatch.setattr(universe, "_lista", list)
    results = universe.search_universe("bitcoin")
    assert results == []

    results = universe.search_universe("AAPL")
    assert results == []


def test_search_respects_limit(monkeypatch):
    many_stocks = [
        {"codigo": f"TST{i}", "nome": f"Teste {i}", "setor": "Finance"} for i in range(20)
    ]
    monkeypatch.setattr(universe, "_lista", lambda: many_stocks)
    results = universe.search_universe("TST", limit=5)
    assert len(results) == 5
