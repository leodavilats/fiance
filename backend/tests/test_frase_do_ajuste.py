from app.analysis.strategy import build_rebalance_suggestions
from app.models import Goal, Opportunity, PortfolioItem


def _alvo(**campos) -> Opportunity:
    base = {
        "ticker": "PETR4",
        "asset_type": "br_stock",
        "price": 30.0,
        "fair_low": 34.5,
        "fair_high": 40.0,
        "margin_of_safety": 0.15,
        "personal_ceiling": 33.0,
        "verdict": "BUY",
        "label": "Abaixo do preço justo",
        "category_resolved": "acoes_br",
        "score": 80.0,
    }
    return Opportunity(**{**base, **campos})


def _sugestoes(alvo: Opportunity) -> dict:
    return build_rebalance_suggestions(
        current_portfolio=[PortfolioItem(ticker="ITSA4", quantity=100, avg_price=10.0)],
        goals=[
            Goal(category="acoes_br", target_pct=60),
            Goal(category="fiis", target_pct=40),
        ],
        opportunities=[alvo],
        portfolio_evaluation={
            "positions": [
                {
                    "ticker": "ITSA4",
                    "category_resolved": "fiis",
                    "verdict": "SELL",
                    "label": "Acima do preço justo",
                    "margin_of_safety": -0.2,
                    "current_price": 10.0,
                    "quantity": 100,
                    "current_value": 1000.0,
                    "reasons": [],
                }
            ]
        },
    )


def test_a_frase_diz_as_duas_margens_e_a_meta_de_renda():
    item = _sugestoes(_alvo())["items"][0]

    assert item["adjustment_sentence"] == (
        "PETR4 está 15% abaixo do preço justo e cabe na sua meta de renda, e você tem ITSA4, "
        "que está 20% acima — avalie se vale fazer o ajuste."
    ), "é a frase-alvo do produto: os dois lados medidos contra o preço justo, e a meta declarada"
    alvo = item["realocar_para"]
    assert (alvo["margin_of_safety"], alvo["fair_low"], alvo["fair_high"]) == (0.15, 34.5, 40.0)
    assert alvo["fits_income_goal"] is True
    assert item["margin_of_safety"] == -0.2


def test_preco_acima_do_teto_da_meta_nao_cabe_na_renda():
    item = _sugestoes(_alvo(personal_ceiling=25.0))["items"][0]

    assert ", mas rende menos que a sua meta de renda," in item["adjustment_sentence"]
    assert item["realocar_para"]["fits_income_goal"] is False


def test_sem_meta_de_renda_declarada_a_frase_nao_fala_dela():
    item = _sugestoes(_alvo(personal_ceiling=None))["items"][0]

    assert "meta de renda" not in item["adjustment_sentence"], (
        "yield desejado não declarado não julga: sem teto pessoal, não há o que caber"
    )
    assert item["realocar_para"]["fits_income_goal"] is None


def test_sem_alvo_nao_ha_frase():
    sugestoes = _sugestoes(_alvo(verdict="HOLD", label="No preço justo"))

    assert sugestoes["items"][0]["adjustment_sentence"] is None
