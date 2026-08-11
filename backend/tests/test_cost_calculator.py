from app.optimizer.cost_calculator import calculate_sell_cost


def test_no_ir_when_no_profit():
    result = calculate_sell_cost("acoes_br", 100, 10.0, 12.0)
    assert result.ir_amount == 0.0
    assert result.gross_profit < 0


def test_acoes_br_isento_ate_20k_no_mes():
    # venda de R$15k, sem vendas anteriores no mês -> ainda dentro da isenção
    result = calculate_sell_cost("acoes_br", 1000, 15.0, 10.0, gross_value_month_before=0)
    assert result.ir_rate == 0.0
    assert result.ir_amount == 0.0


def test_acoes_br_perde_isencao_por_acumulado_mensal():
    # sozinha essa venda de R$15k ficaria isenta, mas já houve R$10k vendidos
    # antes no mês -> acumulado R$25k > 20k -> IR incide
    result = calculate_sell_cost("acoes_br", 1000, 15.0, 10.0, gross_value_month_before=10_000)
    assert result.ir_rate == 0.15
    assert result.ir_amount > 0


def test_fiis_sempre_tributado_sem_isencao():
    result = calculate_sell_cost("fiis", 100, 20.0, 10.0, gross_value_month_before=0)
    assert result.ir_rate == 0.20
    assert result.ir_amount == round((20.0 - 10.0) * 100 * 0.20, 2)


def test_acoes_int_sempre_tributado_sem_isencao():
    result = calculate_sell_cost("acoes_int", 10, 200.0, 100.0, gross_value_month_before=0)
    assert result.ir_rate == 0.15


def test_cripto_isento_ate_35k_no_mes():
    result = calculate_sell_cost("cripto", 1, 30_000.0, 10_000.0, gross_value_month_before=0)
    assert result.ir_rate == 0.0


def test_cripto_perde_isencao_por_acumulado_mensal():
    result = calculate_sell_cost("cripto", 1, 30_000.0, 10_000.0, gross_value_month_before=10_000)
    assert result.ir_rate == 0.15


def test_net_profit_equals_gross_minus_ir():
    result = calculate_sell_cost("fiis", 100, 20.0, 10.0)
    assert result.net_profit == round(result.gross_profit - result.ir_amount, 2)
