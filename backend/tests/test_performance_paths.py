import pytest

from app.core import cache as cache_mod
from app.core import cache_backends
from app.services.snapshot_job import record_snapshot_for_user, run_snapshot_cycle
from app.storage import portfolio_store
from tests.conftest import make_auth_headers

ITEM = {"ticker": "PETR4", "quantity": 100, "avg_price": 30.0, "category": "auto"}


def test_evaluate_does_not_write_snapshots(client):
    headers = make_auth_headers("snap_no_write")
    client.put("/api/portfolio", headers=headers, json={"items": [ITEM]})

    client.post(
        "/api/portfolio/evaluate",
        headers=headers,
        json={"items": [{"ticker": "VALE3", "quantity": 9999, "avg_price": 1.0}]},
    )

    assert client.get("/api/portfolio", headers=headers).json()["snapshots"] == []


def test_dashboard_does_not_write_snapshots(client):
    headers = make_auth_headers("snap_dashboard")
    client.put("/api/portfolio", headers=headers, json={"items": [ITEM]})

    client.get("/api/dashboard", headers=headers)

    assert client.get("/api/portfolio", headers=headers).json()["snapshots"] == []


@pytest.mark.anyio
async def test_snapshot_job_records_stored_positions_plus_fixed_income(client):
    headers = make_auth_headers("snap_job_user")
    client.put("/api/portfolio", headers=headers, json={"items": [ITEM]})
    client.post(
        "/api/fixed-income",
        headers=headers,
        json={
            "nome": "CDB",
            "tipo": "cdb",
            "valor_investido": 5000.0,
            "taxa": 13.0,
            "tipo_taxa": "pre_fixado",
            "data_aplicacao": "2025-01-02",
        },
    )

    assert await record_snapshot_for_user("snap_job_user") is True

    snapshots = client.get("/api/portfolio", headers=headers).json()["snapshots"]
    assert len(snapshots) == 1
    assert snapshots[0]["total_current"] > 3800 + 5000


@pytest.mark.anyio
async def test_snapshot_job_skips_users_without_positions():
    assert await record_snapshot_for_user("snap_empty_user") is False


@pytest.mark.anyio
async def test_snapshot_job_is_idempotent_within_the_day(client):
    headers = make_auth_headers("snap_idempotent")
    client.put("/api/portfolio", headers=headers, json={"items": [ITEM]})

    await record_snapshot_for_user("snap_idempotent")
    await record_snapshot_for_user("snap_idempotent")

    snapshots = client.get("/api/portfolio", headers=headers).json()["snapshots"]
    assert len(snapshots) == 1


@pytest.mark.anyio
async def test_snapshot_cycle_covers_every_tenant(client):
    for uid in ("cycle_a", "cycle_b"):
        client.put("/api/portfolio", headers=make_auth_headers(uid), json={"items": [ITEM]})

    recorded = await run_snapshot_cycle()
    assert recorded >= 2

    for uid in ("cycle_a", "cycle_b"):
        snaps = client.get("/api/portfolio", headers=make_auth_headers(uid)).json()["snapshots"]
        assert len(snaps) == 1


def test_job_lock_excludes_a_second_worker():
    assert portfolio_store.try_acquire_job_lock("test_job", "worker-a", 60) is True
    assert portfolio_store.try_acquire_job_lock("test_job", "worker-b", 60) is False
    assert portfolio_store.try_acquire_job_lock("test_job", "worker-a", 60) is True

    portfolio_store.release_job_lock("test_job", "worker-a")
    assert portfolio_store.try_acquire_job_lock("test_job", "worker-b", 60) is True


def test_job_lock_expires_so_a_dead_worker_does_not_block_forever():
    portfolio_store.try_acquire_job_lock("expiring_job", "worker-dead", -1)
    assert portfolio_store.try_acquire_job_lock("expiring_job", "worker-alive", 60) is True


def test_cache_file_is_separate_from_the_user_database():
    assert cache_mod.DB_PATH.name != "fiance.db"


@pytest.mark.real_cache
def _cache_em(tmp_path, monkeypatch, nome: str):
    monkeypatch.setattr(cache_backends, "DB_PATH", tmp_path / nome)
    cache_mod.reset_connection()
    return cache_mod._sqlite_backend_for_tests()


def test_cache_uses_wal(tmp_path, monkeypatch):
    backend = _cache_em(tmp_path, monkeypatch, "probe.db")

    cache_mod.set("k", {"v": 1}, 60)
    with backend._conn() as cx:
        mode = cx.execute("PRAGMA journal_mode").fetchone()[0]

    assert mode.lower() == "wal"
    cache_mod.reset_connection()


@pytest.mark.real_cache
def test_get_with_age_reports_staleness(tmp_path, monkeypatch):
    _cache_em(tmp_path, monkeypatch, "age.db")

    cache_mod.set("fresh", {"v": 1}, 600)
    value, stale_by = cache_mod.get_with_age("fresh")
    assert value == {"v": 1}
    assert stale_by == 0

    cache_mod.set("old", {"v": 2}, -120)
    value, stale_by = cache_mod.get_with_age("old")
    assert value == {"v": 2}
    assert stale_by > 100

    assert cache_mod.get("old") is None
    assert cache_mod.get_with_age("inexistente") == (None, None)

    cache_mod.reset_connection()


@pytest.mark.real_cache
def test_purge_expired_removes_only_stale_entries(tmp_path, monkeypatch):
    _cache_em(tmp_path, monkeypatch, "purge.db")

    cache_mod.set("keep", 1, 600)
    cache_mod.set("drop", 2, -1)

    assert cache_mod.purge_expired() == 1
    assert cache_mod.get("keep") == 1

    cache_mod.reset_connection()


def test_metrics_endpoint_reports_latency_and_requires_auth(client):
    assert client.get("/api/metrics").status_code == 401

    headers = make_auth_headers("metrics_user")
    client.get("/api/dashboard", headers=headers)

    body = client.get("/api/metrics", headers=headers).json()
    assert body["uptime_seconds"] >= 0
    assert any("/api/dashboard" in route for route in body["latency_by_route"])


def test_responses_carry_a_correlation_id(client):
    headers = make_auth_headers("correlation_user")
    resp = client.get("/api/portfolio", headers=headers)
    assert resp.headers.get("X-Request-Id")

    echoed = client.get("/api/portfolio", headers={**headers, "X-Request-Id": "abc123"})
    assert echoed.headers["X-Request-Id"] == "abc123"


def test_strategy_evaluates_the_portfolio_once_per_request(client, monkeypatch):
    from app.services.portfolio_service import PortfolioService

    calls = {"n": 0}
    original = PortfolioService.evaluate_portfolio

    async def counting(self, req):
        calls["n"] += 1
        return await original(self, req)

    monkeypatch.setattr(PortfolioService, "evaluate_portfolio", counting)

    headers = make_auth_headers("memo_user")
    client.put("/api/portfolio", headers=headers, json={"items": [ITEM]})

    calls["n"] = 0
    resp = client.get("/api/strategy", headers=headers, params={"cash_available": 1000})
    assert resp.status_code == 200
    assert calls["n"] == 1


def test_rebalance_suggestions_share_the_memoized_scan(client, monkeypatch):
    from app.services.opportunity_service import OpportunityService

    calls = {"n": 0}
    original = OpportunityService._scan_universe

    async def counting(self, prefs):
        calls["n"] += 1
        return await original(self, prefs)

    monkeypatch.setattr(OpportunityService, "_scan_universe", counting)

    headers = make_auth_headers("memo_scan_user")
    client.put("/api/portfolio", headers=headers, json={"items": [ITEM]})

    calls["n"] = 0
    assert client.get("/api/rebalance-suggestions", headers=headers).status_code == 200
    assert calls["n"] == 1


def test_sectors_summary_does_not_paginate_a_thousand_items(client):
    headers = make_auth_headers("sectors_user")
    resp = client.get("/api/sectors-summary", headers=headers, params={"category": "acoes_br"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_assets"] >= 0
    for sector in body["sectors"]:
        assert len(sector["top_assets"]) <= 5
