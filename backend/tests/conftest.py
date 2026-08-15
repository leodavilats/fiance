import os
import tempfile

# Usa um arquivo SQLite temporário isolado para os testes, para nunca tocar
# o banco de desenvolvimento (.cache/fiance.db). Precisa ser setado antes
# de qualquer import de app.core.database (que cria o engine no import).
_tmp_db = os.path.join(tempfile.mkdtemp(prefix="fiance_test_"), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.auth import issue_access_token  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import AssetType  # noqa: E402
from app.repositories.asset_repository import AssetRepository  # noqa: E402


@pytest.fixture()
def client():
    """TestClient sobre a app FastAPI real (mesmos middlewares/handlers de erro)."""
    return TestClient(app)


def make_auth_headers(user_id: str) -> dict:
    """Gera um header Authorization válido usando o mesmo emissor de tokens
    usado em produção (app.core.auth.issue_access_token), para que as
    requisições de teste passem de fato pelo Depends(get_current_user)."""
    token = issue_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth_headers():
    return make_auth_headers("test_http_user")


# Snapshots fake para os tickers usados nos testes de API — evita qualquer
# chamada de rede real (BRAPI/Finnhub/CoinGecko) durante os testes HTTP.
def _fake_snapshot(symbol: str):
    from app.collectors.universal import AssetSnapshot

    catalog = {
        "PETR4": AssetSnapshot(
            symbol="PETR4",
            yf_symbol="PETR4.SA",
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
            roe=0.2,
            dividend_yield=12.0,
            debt_to_equity=0.6,
            profit_margin=0.25,
            revenue_growth=0.05,
            fifty_two_week_high=42.0,
            fifty_two_week_low=30.0,
        ),
        "VALE3": AssetSnapshot(
            symbol="VALE3",
            yf_symbol="VALE3.SA",
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
            roe=0.25,
            dividend_yield=9.0,
            debt_to_equity=0.4,
            profit_margin=0.3,
            revenue_growth=0.03,
            fifty_two_week_high=70.0,
            fifty_two_week_low=55.0,
        ),
    }
    return catalog.get(symbol.upper())


@pytest.fixture(autouse=True)
def _stub_market_data(monkeypatch):
    """Isola os testes de qualquer chamada de rede real para dados de mercado.

    Vale para todos os testes (novos e antigos): faz um universo fixo e
    pequeno (PETR4, VALE3) responder com dados determinísticos, e qualquer
    outro ticker responder com None/[] (equivalente a "sem dados" — já
    tratado com fallback pelo código de produção).
    """

    async def _fake_get_asset(symbol: str):
        return _fake_snapshot(symbol)

    async def _fake_get_dividends(symbol: str):
        return []

    async def _fake_get_history(symbol: str, period: str = "1y"):
        return {}

    async def _fake_get_universe(symbols: list[str]):
        return [s for s in (_fake_snapshot(sym) for sym in symbols) if s is not None]

    monkeypatch.setattr(AssetRepository, "get_asset", staticmethod(_fake_get_asset))
    monkeypatch.setattr(AssetRepository, "get_dividends", staticmethod(_fake_get_dividends))
    monkeypatch.setattr(AssetRepository, "get_history", staticmethod(_fake_get_history))
    monkeypatch.setattr(AssetRepository, "get_universe", staticmethod(_fake_get_universe))

    import app.services.opportunity_service as opp_mod

    monkeypatch.setattr(opp_mod, "get_universe", lambda: ["PETR4", "VALE3"])

    # Cache de oportunidades/universo é um sqlite em disco compartilhado com o
    # ambiente de dev — troca por um dicionário em memória isolado por teste.
    import app.core.cache as cache_mod

    fake_store: dict = {}
    monkeypatch.setattr(cache_mod, "get", lambda key: fake_store.get(key))
    monkeypatch.setattr(
        cache_mod, "set", lambda key, value, ttl_seconds: fake_store.__setitem__(key, value)
    )
    monkeypatch.setattr(cache_mod, "delete", lambda key: fake_store.pop(key, None))
    monkeypatch.setattr(cache_mod, "clear_all", lambda: fake_store.clear())
