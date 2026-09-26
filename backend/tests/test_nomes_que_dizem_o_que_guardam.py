from __future__ import annotations

from datetime import UTC, datetime

from app.analysis.fair_price import RATE_BASE_AVERAGE, ValuationRates, compute_fair_price
from app.models.analysis import FairPriceBlock

REF = datetime(2026, 9, 23, 15, tzinfo=UTC)

TAXAS = ValuationRates(
    discount_rate=0.145, fii_yield=0.095, rate_base=RATE_BASE_AVERAGE, selic_pct=9.5
)


def _acao():
    return compute_fair_price(
        price=10.0,
        eps=1.0,
        book_value=8.0,
        dividends=[{"date": f"{2021 + i}-06-01", "value": 0.5} for i in range(5)],
        asset_type="br_stock",
        net_income_history=[120.0] * 3,
        equity_history=[800.0] * 3,
        net_income_ttm=120.0,
        rates=TAXAS,
        reference=REF,
    )


def test_os_nomes_novos_chegam_a_resposta():
    bloco = FairPriceBlock(**_acao().__dict__)

    assert bloco.principal_value is not None, (
        "campo calculado que o modelo Pydantic não declara some em silêncio no construtor"
    )
    assert bloco.dividend_recurring is not None
    assert bloco.dividend_yield_recurring is not None


def test_os_nomes_antigos_seguem_como_alias():
    bloco = FairPriceBlock(**_acao().__dict__)

    assert bloco.consensus == bloco.principal_value, (
        "o app em loja lê `consensus`: tirar o alias antes da versão nova apaga o preço justo "
        "da tela de quem não atualizou"
    )
    assert bloco.avg_dividend_5y == bloco.dividend_recurring
    assert bloco.dy_5y == bloco.dividend_yield_recurring
