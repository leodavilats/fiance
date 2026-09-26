from __future__ import annotations

from app.analysis.scoring import FII_WEIGHTS, score_opportunity
from app.models.enums import RiskProfile


def _fii(perfil: RiskProfile, margem: float = 0.0, dy: float = 12.0) -> float:
    score, _ = score_opportunity(
        asset_type="fii",
        margin_of_safety=margem,
        dividend_yield=dy,
        roe=None,
        profit_margin=None,
        debt_to_equity=None,
        revenue_growth=None,
        profile=perfil,
    )
    return score


def test_o_perfil_de_risco_muda_o_score_do_fii():
    conservador = _fii(RiskProfile.conservative)
    arrojado = _fii(RiskProfile.aggressive)

    assert conservador > arrojado, (
        "FII de renda alta e sem desconto: o conservador, que pesa a renda, pontua mais que o "
        "arrojado, que pesa o desconto. Antes, trocar de perfil não mudava nada"
    )


def test_no_arrojado_o_desconto_pesa_mais():
    assert _fii(RiskProfile.aggressive, margem=0.3, dy=6.0) > _fii(
        RiskProfile.conservative, margem=0.3, dy=6.0
    )


def test_o_fii_so_pesa_o_que_a_fonte_entrega():
    for pesos in FII_WEIGHTS.values():
        assert set(pesos) == {"mos", "dividend"}, (
            "a BRAPI não entrega valor de mercado de FII (0 de 6 na amostra de 2026-09-25): "
            "dimensão que nunca tem dado só derruba a completude"
        )


def test_etf_nao_tem_score():
    score, detalhe = score_opportunity(
        asset_type="etf",
        margin_of_safety=None,
        dividend_yield=10.0,
        roe=None,
        profit_margin=None,
        debt_to_equity=None,
        revenue_growth=None,
    )

    assert score == 0.0 and detalhe["data_completeness"] == 0.0, (
        "ETF não tem preço justo (ADR-014) e a fonte não entrega fundamento dele: uma nota só de "
        "dividendo leria como oportunidade o que é política de distribuição do fundo"
    )
