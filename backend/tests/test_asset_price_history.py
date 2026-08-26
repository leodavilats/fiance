"""A série de preços precisa chegar ao cliente — e só onde faz sentido.

O histórico já era buscado para calcular médias móveis e descartado logo depois,
então a página do ativo não tinha como desenhar preço contra preço justo. Estes
testes travam as duas metades da decisão: o campo existe no contrato, e
`/compare` continua sem ele (N séries diárias de 2 anos não cabem numa
comparação).
"""

from __future__ import annotations

from app.models import AssetAnalysis, PricePoint


def test_price_point_is_part_of_the_asset_contract():
    fields = AssetAnalysis.model_fields
    assert "price_history" in fields


def test_price_history_defaults_to_empty_not_none():
    """Ausência de série é lista vazia: o cliente checa tamanho, não `None`."""
    from app.models import DecisionBlock, FairPriceBlock, TechnicalBlock

    analysis = AssetAnalysis(
        symbol="PETR4",
        asset_type="br_stock",
        fair_price=FairPriceBlock(),
        technical=TechnicalBlock(),
        decision=DecisionBlock(verdict="HOLD", label="Manter", confidence=0.5, reasons=[]),
    )

    assert analysis.price_history == []


def test_price_points_keep_date_and_close():
    point = PricePoint(date="2026-08-25", close=31.42)

    assert point.date == "2026-08-25"
    assert point.close == 31.42
