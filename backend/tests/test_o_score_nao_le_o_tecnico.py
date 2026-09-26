from __future__ import annotations

import inspect

import pytest

from app.analysis.scoring import OPPORTUNITY_WEIGHTS, score_opportunity
from app.models.enums import RiskProfile


@pytest.mark.parametrize("perfil", list(RiskProfile))
def test_nenhum_perfil_pesa_o_tecnico(perfil):
    assert "technical" not in OPPORTUNITY_WEIGHTS[perfil], (
        "o score ordena Descobrir e decide o destaque: RSI e tendência ali são o técnico "
        "decidindo, que é o que a leitura de valor proíbe"
    )


def test_o_score_nem_recebe_rsi_nem_tendencia():
    parametros = inspect.signature(score_opportunity).parameters

    assert "rsi_14" not in parametros and "trend" not in parametros


def test_bdr_sem_faixa_e_sem_fundamento_nao_ganha_nota():
    score, detalhe = score_opportunity(
        asset_type="bdr",
        margin_of_safety=None,
        dividend_yield=None,
        roe=None,
        profit_margin=None,
        debt_to_equity=None,
        revenue_growth=None,
        market_cap=None,
    )

    assert score == 0.0 and detalhe["data_completeness"] == 0.0, (
        "medido em 2026-09-25: o score de MSFT34 era 57,8, e todo ele vinha do RSI e da "
        "tendência, porque BDR não tem preço justo nem fundamento na fonte"
    )
