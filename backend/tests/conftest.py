import os
import tempfile

_tmp_db = os.path.join(tempfile.mkdtemp(prefix="fiance_test_"), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ.setdefault("APP_ENV", "development")

from datetime import UTC, datetime, timedelta  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.auth import issue_access_token  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import AssetType  # noqa: E402
from app.repositories.asset_repository import AssetRepository  # noqa: E402


@pytest.fixture()
def client():
    return TestClient(app)


def make_auth_headers(user_id: str) -> dict:
    token = issue_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth_headers():
    return make_auth_headers("test_http_user")


def _fake_snapshot(symbol: str):
    from app.collectors.universal import AssetSnapshot

    catalog = {
        "PETR4": AssetSnapshot(
            symbol="PETR4",
            asset_type=AssetType.br_stock,
            name="Petrobras PN",
            sector="Petróleo, Gás e Biocombustíveis",
            currency="BRL",
            price=38.0,
            market_cap=5.0e11,
            pe_ratio=6.0,
            pb_ratio=1.2,
            eps=6.3,
            book_value=31.0,
            roe=20.0,
            dividend_yield=12.0,
            debt_to_equity=60.0,
            profit_margin=25.0,
            revenue_growth=5.0,
            fifty_two_week_high=42.0,
            fifty_two_week_low=30.0,
        ),
        "VALE3": AssetSnapshot(
            symbol="VALE3",
            asset_type=AssetType.br_stock,
            name="Vale ON",
            sector="Mineração",
            currency="BRL",
            price=60.0,
            market_cap=2.5e11,
            pe_ratio=5.0,
            pb_ratio=1.5,
            eps=12.0,
            book_value=40.0,
            roe=25.0,
            dividend_yield=9.0,
            debt_to_equity=40.0,
            profit_margin=30.0,
            revenue_growth=3.0,
            fifty_two_week_high=70.0,
            fifty_two_week_low=55.0,
        ),
    }
    return catalog.get(symbol.upper())


def build_quarterly_dividends(
    years: int = 4,
    per_payment: float = 0.75,
    reference: datetime | None = None,
) -> list[dict]:
    today = reference or datetime.now(UTC)
    out: list[dict] = []
    for year_offset in range(1, years + 1):
        year = today.year - year_offset
        for month in (2, 5, 8, 11):
            out.append({"date": f"{year}-{month:02d}-15", "value": per_payment})
    return sorted(out, key=lambda d: d["date"])


def build_daily_history(days: int, start: float = 30.0, step: float = 0.05) -> dict[str, float]:
    today = datetime.now(UTC)
    return {
        (today - timedelta(days=days - i)).strftime("%Y-%m-%d"): round(start + i * step, 4)
        for i in range(days)
    }


_FAKE_DIVIDENDS = {"PETR4": build_quarterly_dividends()}
_FAKE_HISTORY = {"PETR4": build_daily_history(260)}


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "real_cache: usa a implementação real de cache em vez do dicionário em memória",
    )


@pytest.fixture()
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def _stub_market_data(monkeypatch, request):

    async def _fake_get_asset(symbol: str):
        return _fake_snapshot(symbol)

    async def _fake_get_dividends(symbol: str):
        return list(_FAKE_DIVIDENDS.get(symbol.upper(), []))

    async def _fake_get_history(symbol: str, period: str = "1y"):
        return dict(_FAKE_HISTORY.get(symbol.upper(), {}))

    async def _fake_get_universe(symbols: list[str]):
        return [s for s in (_fake_snapshot(sym) for sym in symbols) if s is not None]

    monkeypatch.setattr(AssetRepository, "get_asset", staticmethod(_fake_get_asset))
    monkeypatch.setattr(AssetRepository, "get_dividends", staticmethod(_fake_get_dividends))
    monkeypatch.setattr(AssetRepository, "get_history", staticmethod(_fake_get_history))
    monkeypatch.setattr(AssetRepository, "get_universe", staticmethod(_fake_get_universe))

    import app.services.opportunity_service as opp_mod

    monkeypatch.setattr(opp_mod, "get_universe", lambda: ["PETR4", "VALE3"])

    from app.core.universe import invalidate_universe_memo

    invalidate_universe_memo()

    import app.core.cache as cache_mod

    if request.node.get_closest_marker("real_cache"):
        return

    fake_store: dict = {}
    monkeypatch.setattr(cache_mod, "get", lambda key: fake_store.get(key))
    monkeypatch.setattr(
        cache_mod,
        "get_with_age",
        lambda key: (fake_store.get(key), 0.0 if key in fake_store else None),
    )
    monkeypatch.setattr(
        cache_mod, "set", lambda key, value, ttl_seconds: fake_store.__setitem__(key, value)
    )
    monkeypatch.setattr(cache_mod, "delete", lambda key: fake_store.pop(key, None))
    monkeypatch.setattr(cache_mod, "clear_all", lambda: fake_store.clear())
    monkeypatch.setattr(cache_mod, "delete_pattern", lambda pattern: 0)

    fake_rates = {
        "cdi_anual": 14.40,
        "selic_anual": 14.40,
        "ipca_anual": 5.00,
        "source": "estimativa",
    }
    import app.analysis.renda_fixa_analysis as rf_mod
    import app.collectors.rates as rates_mod
    import app.services.benchmark_service as bench_mod
    import app.services.fixed_income_service as fi_mod

    monkeypatch.setattr(rates_mod, "get_rates", lambda: dict(fake_rates))
    monkeypatch.setattr(rf_mod, "get_rates", lambda: dict(fake_rates))
    monkeypatch.setattr(fi_mod, "get_rates", lambda: dict(fake_rates))
    monkeypatch.setattr(bench_mod, "get_rates", lambda: dict(fake_rates))
