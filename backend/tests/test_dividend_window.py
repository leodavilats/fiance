"""Regressões da janela de dividendos (D4)."""

from datetime import UTC, datetime

from app.analysis.fair_price import (
    average_dividend_last_12m,
    average_dividend_last_n_years,
    bazin_fair_price,
    compute_fair_price,
)
from app.collectors.universal import _sum_dividends_last_12m

REFERENCE = datetime(2026, 7, 1, tzinfo=UTC)


def _yearly(year: int, total: float) -> list[dict]:
    """Um pagamento por trimestre somando `total` no ano."""
    return [{"date": f"{year}-{m:02d}-15", "value": total / 4} for m in (2, 5, 8, 11)]


def test_average_over_six_years_of_data_uses_the_five_year_window():
    dividends = []
    for year in range(2019, 2026):
        dividends += _yearly(year, 4.0)

    assert average_dividend_last_n_years(dividends, reference=REFERENCE) == 4.0


def test_average_with_three_years_of_history_is_not_diluted_by_fixed_denominator():
    """Uma empresa com 3 anos de histórico tinha a média subestimada em ~40%."""
    dividends = _yearly(2023, 4.0) + _yearly(2024, 4.0) + _yearly(2025, 4.0)

    assert average_dividend_last_n_years(dividends, reference=REFERENCE) == 4.0


def test_current_partial_year_does_not_drag_the_average_down():
    """O ano corrente não é contado como cheio."""
    full_years = _yearly(2024, 4.0) + _yearly(2025, 4.0)
    partial_current = [{"date": "2026-02-15", "value": 1.0}]

    only_complete = average_dividend_last_n_years(full_years, reference=REFERENCE)
    with_partial = average_dividend_last_n_years(full_years + partial_current, reference=REFERENCE)

    assert only_complete == 4.0
    assert with_partial == 4.0


def test_year_without_payment_inside_the_covered_span_counts_as_zero():
    """Buraco no meio do histórico é ausência real de provento, não de dado."""
    dividends = _yearly(2023, 6.0) + _yearly(2025, 6.0)

    assert average_dividend_last_n_years(dividends, reference=REFERENCE) == 4.0


def test_asset_without_any_complete_year_falls_back_to_trailing_12m():
    """IPO recente: devolver None apagaria o Bazin de um ativo que paga."""
    dividends = [{"date": "2026-03-10", "value": 0.5}, {"date": "2026-06-10", "value": 0.5}]

    assert average_dividend_last_n_years(dividends, reference=REFERENCE) == 1.0


def test_average_is_none_without_any_dividend():
    assert average_dividend_last_n_years([], reference=REFERENCE) is None


def test_trailing_12m_ignores_older_payments():
    dividends = [
        {"date": "2024-01-10", "value": 9.0},
        {"date": "2025-09-10", "value": 1.0},
        {"date": "2026-03-10", "value": 2.0},
    ]

    assert average_dividend_last_12m(dividends, reference=REFERENCE) == 3.0


def test_bazin_reflects_the_corrected_average():
    dividends = _yearly(2024, 4.0) + _yearly(2025, 4.0)
    avg = average_dividend_last_n_years(dividends, reference=REFERENCE)

    result = compute_fair_price(
        price=50.0,
        eps=None,
        book_value=None,
        dividends=dividends,
        asset_type="etf",
        reference=REFERENCE,
    )

    assert result.bazin == bazin_fair_price(avg, 0.04)


def test_collector_dy_uses_last_12_months_not_first_12_records():
    """Regressão do `cashDividends[:12]`."""
    raw = {
        "dividendsData": {
            "cashDividends": [
                {"paymentDate": f"{year}-{month:02d}-15", "rate": 1.0}
                for year in (2023, 2024, 2025, 2026)
                for month in (2, 5, 8, 11)
            ]
        }
    }

    total = _sum_dividends_last_12m(raw, reference=REFERENCE)

    assert total == 4.0
