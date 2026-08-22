import asyncio

import pytest

from app.models import SellRequest
from app.services.portfolio_service import PortfolioService
from app.storage import portfolio_store


def _new_service(monkeypatch, asset_type="br_stock"):
    service = PortfolioService()

    class _FakeSnap:
        def __init__(self, asset_type):
            self.asset_type = asset_type

    async def _fake_get_asset(ticker):
        return _FakeSnap(asset_type)

    monkeypatch.setattr(service.asset_repo, "get_asset", _fake_get_asset)
    return service


def test_sell_partial_reduces_quantity(monkeypatch):
    uid = "test_sell_partial"
    portfolio_store.upsert_position("PETR4", quantity=100, avg_price=10.0, user_id=uid)
    service = _new_service(monkeypatch)

    req = SellRequest(ticker="PETR4", quantity=40, sell_price=15.0)

    from app.core.context import reset_current_user_id, set_current_user_id

    token = set_current_user_id(uid)
    try:
        trade = asyncio.run(service.sell_position(req))
    finally:
        reset_current_user_id(token)

    assert trade.quantity == 40
    assert trade.gross_profit == (15.0 - 10.0) * 40

    remaining = portfolio_store.get_position("PETR4", user_id=uid)
    assert remaining is not None
    assert remaining["quantity"] == 60


def test_sell_all_removes_position(monkeypatch):
    uid = "test_sell_all"
    portfolio_store.upsert_position("VALE3", quantity=50, avg_price=20.0, user_id=uid)
    service = _new_service(monkeypatch)

    from app.core.context import reset_current_user_id, set_current_user_id

    req = SellRequest(ticker="VALE3", quantity=50, sell_price=25.0)
    token = set_current_user_id(uid)
    try:
        asyncio.run(service.sell_position(req))
    finally:
        reset_current_user_id(token)

    assert portfolio_store.get_position("VALE3", user_id=uid) is None


def test_sell_more_than_owned_raises(monkeypatch):
    uid = "test_sell_too_much"
    portfolio_store.upsert_position("ITUB4", quantity=10, avg_price=20.0, user_id=uid)
    service = _new_service(monkeypatch)

    from app.core.context import reset_current_user_id, set_current_user_id

    req = SellRequest(ticker="ITUB4", quantity=999, sell_price=25.0)
    token = set_current_user_id(uid)
    try:
        with pytest.raises(ValueError):
            asyncio.run(service.sell_position(req))
    finally:
        reset_current_user_id(token)


def test_sell_unknown_ticker_raises(monkeypatch):
    uid = "test_sell_unknown"
    service = _new_service(monkeypatch)

    from app.core.context import reset_current_user_id, set_current_user_id

    req = SellRequest(ticker="NOPE99", quantity=1, sell_price=1.0)
    token = set_current_user_id(uid)
    try:
        with pytest.raises(ValueError):
            asyncio.run(service.sell_position(req))
    finally:
        reset_current_user_id(token)


def test_closed_trades_totals(monkeypatch):
    uid = "test_closed_trades_totals"
    portfolio_store.upsert_position("BBAS3", quantity=100, avg_price=10.0, user_id=uid)
    service = _new_service(monkeypatch)

    from app.core.context import reset_current_user_id, set_current_user_id

    req = SellRequest(ticker="BBAS3", quantity=100, sell_price=12.0)
    token = set_current_user_id(uid)
    try:
        asyncio.run(service.sell_position(req))
        response = service.get_closed_trades()
    finally:
        reset_current_user_id(token)

    assert len(response.trades) == 1
    assert response.total_realized_pnl == response.trades[0].net_profit
