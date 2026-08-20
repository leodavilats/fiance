import os
import tempfile

# Usa um arquivo SQLite temporário isolado para os testes, para nunca tocar
# o banco de desenvolvimento (.cache/fiance.db). Precisa ser setado antes
# de qualquer import de app.core.database (que cria o engine no import).
_tmp_db = os.path.join(tempfile.mkdtemp(prefix="fiance_test_"), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"

from datetime import UTC, datetime, timedelta  # noqa: E402

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
# chamada de rede real (BRAPI) durante os testes HTTP.
#
# Unidades: roe / profit_margin / revenue_growth / debt_to_equity vêm do
# collector já em **percentual** (ver collectors.universal._ratio_to_pct), e é
# nessa escala que scoring e fair price esperam receber.
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
    """Histórico trimestral de proventos terminando no ano completo anterior.

    O stub original devolvia `[]` para todos os tickers, então nenhum teste
    passava por average_dividend_last_n_years com dado real nem pelo cálculo de
    DY do collector — exatamente onde estavam os bugs de valuation.
    """
    today = reference or datetime.now(UTC)
    out: list[dict] = []
    for year_offset in range(1, years + 1):
        year = today.year - year_offset
        for month in (2, 5, 8, 11):
            out.append({"date": f"{year}-{month:02d}-15", "value": per_payment})
    return sorted(out, key=lambda d: d["date"])


def build_daily_history(days: int, start: float = 30.0, step: float = 0.05) -> dict[str, float]:
    """Série diária sintética e monotônica — SMA/RSI determinísticos."""
    today = datetime.now(UTC)
    return {
        (today - timedelta(days=days - i)).strftime("%Y-%m-%d"): round(start + i * step, 4)
        for i in range(days)
    }


_FAKE_DIVIDENDS = {"PETR4": build_quarterly_dividends()}
_FAKE_HISTORY = {"PETR4": build_daily_history(260)}


@pytest.fixture(autouse=True)
def _stub_market_data(monkeypatch):
    """Isola os testes de qualquer chamada de rede real para dados de mercado.

    Vale para todos os testes: faz um universo fixo e pequeno (PETR4, VALE3)
    responder com dados determinísticos, e qualquer outro ticker responder com
    None/[] (equivalente a "sem dados" — já tratado com fallback pelo código de
    produção). PETR4 traz histórico de dividendos e série de preços; VALE3 fica
    sem nenhum dos dois, cobrindo os dois caminhos.
    """

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

    # Índices de setor/autocomplete são memoizados em processo — sem limpar,
    # um teste herda o índice construído pelo anterior.
    from app.core.universe import invalidate_universe_memo

    invalidate_universe_memo()

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
    monkeypatch.setattr(cache_mod, "delete_pattern", lambda pattern: 0)
