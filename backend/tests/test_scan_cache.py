"""Stale-while-revalidate no scan do universo.

`GET /dashboard` em cache frio disparava o scan do universo inteiro **dentro do
request**: ~280 tickers × httpx com timeout de 15 s. O usuário pagava o scan, e
o interceptor do web precisava de um timeout de 300 s para acomodar isso.
"""

import asyncio

import pytest

import app.services.opportunity_service as opp_mod
from app.services import OpportunityService


@pytest.fixture()
def service():
    return OpportunityService()


@pytest.fixture(autouse=True)
def _reset_refresh_state():
    opp_mod._refresh_task = None
    yield
    opp_mod._refresh_task = None


@pytest.mark.anyio
async def test_fresh_cache_is_served_without_refetching(service, monkeypatch):
    fetches = {"n": 0}

    original = OpportunityService._fetch_market_record

    async def counting(self, symbol):
        fetches["n"] += 1
        return await original(self, symbol)

    monkeypatch.setattr(OpportunityService, "_fetch_market_record", counting)

    await service._scan_market()
    first_round = fetches["n"]
    assert first_round > 0

    await service._scan_market()
    assert fetches["n"] == first_round


@pytest.mark.anyio
async def test_stale_cache_is_served_immediately_and_revalidated(service, monkeypatch):
    # Primeiro scan popula o cache.
    records, universe_size = await service._scan_market()
    assert records

    stale_payload = {
        "items": [r.to_dict() for r in records],
        "universe_size": universe_size,
    }

    # Cache vencido há 1 h, dentro da tolerância de stale.
    monkeypatch.setattr(opp_mod.cache, "get_with_age", lambda key: (stale_payload, 3600.0))

    refreshed = asyncio.Event()

    async def fake_refresh(self):
        refreshed.set()
        return records, universe_size

    monkeypatch.setattr(OpportunityService, "_refresh_market", fake_refresh)

    served, size = await service._scan_market()

    # Serviu o valor antigo sem esperar o recálculo.
    assert len(served) == len(records)
    assert size == universe_size

    await asyncio.wait_for(refreshed.wait(), timeout=2)


@pytest.mark.anyio
async def test_too_stale_cache_is_recalculated_synchronously(service, monkeypatch):
    records, universe_size = await service._scan_market()
    payload = {"items": [r.to_dict() for r in records], "universe_size": universe_size}

    # Muito além da tolerância: não vale servir dado tão velho.
    monkeypatch.setattr(
        opp_mod.cache,
        "get_with_age",
        lambda key: (payload, opp_mod._SCAN_STALE_TOLERANCE + 1),
    )

    refreshed = {"called": False}

    async def fake_refresh(self):
        refreshed["called"] = True
        return records, universe_size

    monkeypatch.setattr(OpportunityService, "_refresh_market", fake_refresh)

    await service._scan_market()
    assert refreshed["called"] is True


@pytest.mark.anyio
async def test_only_one_background_refresh_runs_at_a_time(service, monkeypatch):
    records, universe_size = await service._scan_market()
    payload = {"items": [r.to_dict() for r in records], "universe_size": universe_size}

    monkeypatch.setattr(opp_mod.cache, "get_with_age", lambda key: (payload, 3600.0))

    started = asyncio.Event()
    release = asyncio.Event()
    calls = {"n": 0}

    async def slow_refresh(self):
        calls["n"] += 1
        started.set()
        await release.wait()
        return records, universe_size

    monkeypatch.setattr(OpportunityService, "_refresh_market", slow_refresh)

    await asyncio.gather(*[service._scan_market() for _ in range(5)])
    await asyncio.wait_for(started.wait(), timeout=2)

    release.set()
    if opp_mod._refresh_task is not None:
        await opp_mod._refresh_task

    # Cinco requests simultâneas em cache vencido não devem virar cinco scans.
    assert calls["n"] == 1


@pytest.mark.anyio
async def test_empty_cache_pays_the_scan(service, monkeypatch):
    monkeypatch.setattr(opp_mod.cache, "get_with_age", lambda key: (None, None))

    called = {"n": 0}

    async def fake_refresh(self):
        called["n"] += 1
        return [], 0

    monkeypatch.setattr(OpportunityService, "_refresh_market", fake_refresh)

    await service._scan_market()
    assert called["n"] == 1
