"""O diagnóstico de queda precisa dizer *por que* caiu, não só *quanto*.

Uma queda com fundamento preservado e uma queda com fundamento deteriorado são
decisões opostas, e a lista achatada de `reasons` não permitia distingui-las no
cliente. Estes testes travam o agrupamento e garantem que ele continua sendo a
mesma informação — nenhum motivo criado, nenhum perdido.
"""

from __future__ import annotations

from app.analysis.dip_analysis import compute_dip_analysis

GROUPS = {"value", "quality", "technical", "dividend", "news"}


def _analyze(**overrides):
    base = {
        "margin_of_safety": 0.30,
        "roe": 18.0,
        "profit_margin": 12.0,
        "debt_to_equity": 0.4,
        "rsi_14": 28.0,
        "trend": "downtrend",
        "distance_from_52w_high_pct": -32.0,
        "sma_200": 30.0,
        "last_price": 22.0,
        "dividend_yield": 7.0,
        "avg_dividend_5y": 1.4,
        "fair_price_consensus": 32.0,
        "current_price": 22.0,
        "news_items": [],
        "news_sentiment_summary": "",
        "asset_type": "br_stock",
    }
    base.update(overrides)
    return compute_dip_analysis(**base)


def test_reason_groups_cover_every_dimension():
    result = _analyze()

    assert set(result.reason_groups) == GROUPS


def test_reason_groups_are_the_same_reasons_not_new_ones():
    """Agrupar é apresentação: nenhum texto novo, nenhum texto perdido."""
    result = _analyze()

    flattened = [r for group in result.reason_groups.values() for r in group]

    assert flattened == result.reasons

    etf = _analyze(asset_type="etf")
    etf_flat = [r for group in etf.reason_groups.values() for r in group]
    assert etf_flat == etf.reasons[1:]
    assert "ETF" in etf.reasons[0]


def test_quality_dimension_separates_fundamento_de_preco():
    """A queda aritmética vive em `technical`; a deterioração, em `quality`."""
    deteriorated = _analyze(roe=3.0, profit_margin=1.0, debt_to_equity=2.5)

    quality = " ".join(deteriorated.reason_groups["quality"])
    technical = " ".join(deteriorated.reason_groups["technical"])

    assert "ROE baixo" in quality
    assert "Alto endividamento" in quality
    assert "52 semanas" in technical
    assert "ROE" not in technical


def test_missing_inputs_land_as_indisponivel_not_as_bad_score():
    """Dado ausente é estado, não nota ruim (§11)."""
    blind = _analyze(roe=None, profit_margin=None, debt_to_equity=None)

    quality = blind.reason_groups["quality"]

    assert all("indisponível" in r for r in quality)
    assert blind.breakdown.quality_score == 0.0
