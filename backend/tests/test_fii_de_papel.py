from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.analysis.decision import decide
from app.analysis.fair_price import (
    INFLATION_TARGET,
    RATE_BASE_AVERAGE,
    ValuationRates,
    compute_fair_price,
)
from app.analysis.fii_segments import PAPER_FIIS, SEGMENT_PAPER, fii_segment

REF = datetime(2026, 9, 23, 15, tzinfo=UTC)

TAXAS = ValuationRates(
    discount_rate=0.145, fii_yield=0.095, rate_base=RATE_BASE_AVERAGE, selic_pct=9.5
)


def _fii(simbolo: str):
    return compute_fair_price(
        price=9.0,
        eps=None,
        book_value=10.0,
        dividends=[{"date": f"{2021 + i}-06-01", "value": 1.2} for i in range(5)],
        asset_type="fii",
        rates=TAXAS,
        reference=REF,
        symbol=simbolo,
    )


def test_fii_de_papel_exige_yield_nominal():
    papel = _fii("MXRF11")

    assert papel.premises["fii_segment"] == SEGMENT_PAPER
    assert papel.premises["fii_yield"] == pytest.approx(TAXAS.fii_yield + INFLATION_TARGET), (
        "a distribuição do FII de papel já traz a correção monetária dos recebíveis, e o principal "
        "não cresce com ela: capitalizá-la por juro real a lia como renda que cresce com a "
        "inflação, e todo FII de papel parecia barato"
    )


def test_o_mesmo_fluxo_vale_menos_num_fundo_de_papel():
    assert _fii("MXRF11").principal_value < _fii("HGLG11").principal_value


def test_fii_fora_da_lista_segue_como_tijolo_e_se_declara():
    tijolo = _fii("HGLG11")

    assert tijolo.premises["fii_segment"] == "nao_classificado"
    assert tijolo.premises["fii_yield"] == TAXAS.fii_yield


def test_a_razao_diz_por_que_o_yield_inclui_a_inflacao():
    dec = decide(_fii("MXRF11"), current_price=9.0)

    assert any("fundo é de papel" in r for r in dec.reasons)


def test_a_lista_so_tem_fii():
    assert all(t.endswith("11") for t in PAPER_FIIS)
    assert fii_segment("mxrf11.SA") == SEGMENT_PAPER, "o ticker vem em qualquer caixa e com sufixo"
