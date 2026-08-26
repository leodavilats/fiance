"""Apuração de IR: mês da operação, isenção e prejuízo compensável."""

import time

from app.core.brt import month_bounds, to_brt
from app.models.enums import AssetCategory
from app.optimizer.cost_calculator import ISENCAO_MENSAL_ACOES, calculate_sell_cost
from app.storage import portfolio_store
from tests.conftest import make_auth_headers

ACOES = AssetCategory.acoes_br.value
FIIS = AssetCategory.fiis.value


def _last_month_timestamp() -> float:
    month_start, _ = month_bounds()
    return month_start - 5 * 86400


def test_gross_sales_are_scoped_to_the_month_of_the_sale():
    user = "tax_month_scope"
    now = time.time()
    last_month = _last_month_timestamp()

    portfolio_store.create_closed_trade(
        ticker="PETR4",
        category=ACOES,
        quantity=100,
        avg_price=10.0,
        sell_price=30.0,
        gross_profit=2000.0,
        ir_rate=0.0,
        ir_amount=0.0,
        net_profit=2000.0,
        sold_at=last_month,
        user_id=user,
    )
    portfolio_store.create_closed_trade(
        ticker="VALE3",
        category=ACOES,
        quantity=10,
        avg_price=10.0,
        sell_price=20.0,
        gross_profit=100.0,
        ir_rate=0.0,
        ir_amount=0.0,
        net_profit=100.0,
        sold_at=now,
        user_id=user,
    )

    assert portfolio_store.sum_gross_sales_in_month(ACOES, at=last_month, user_id=user) == 3000.0
    assert portfolio_store.sum_gross_sales_in_month(ACOES, at=now, user_id=user) == 200.0


def test_backdated_sale_is_taxed_against_its_own_month(client):
    user = "tax_backdate_user"
    headers = make_auth_headers(user)
    last_month = _last_month_timestamp()

    portfolio_store.create_closed_trade(
        ticker="VALE3",
        category=ACOES,
        quantity=1000,
        avg_price=10.0,
        sell_price=30.0,
        gross_profit=20_000.0,
        ir_rate=0.15,
        ir_amount=3_000.0,
        net_profit=17_000.0,
        sold_at=last_month,
        user_id=user,
    )

    client.post(
        "/api/portfolio/position",
        headers=headers,
        json={"ticker": "PETR4", "quantity": 200, "avg_price": 10.0, "category": "acoes_br"},
    )
    resp = client.post(
        "/api/portfolio/sell",
        headers=headers,
        json={
            "ticker": "PETR4",
            "quantity": 100,
            "sell_price": 30.0,
            "sold_at": last_month + 3600,
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["ir_amount"] > 0, "venda retroativa herdou a isenção do mês corrente"


def test_current_month_sale_is_not_polluted_by_another_month(client):
    user = "tax_current_month_user"
    headers = make_auth_headers(user)

    portfolio_store.create_closed_trade(
        ticker="VALE3",
        category=ACOES,
        quantity=1000,
        avg_price=10.0,
        sell_price=30.0,
        gross_profit=20_000.0,
        ir_rate=0.15,
        ir_amount=3_000.0,
        net_profit=17_000.0,
        sold_at=_last_month_timestamp(),
        user_id=user,
    )

    client.post(
        "/api/portfolio/position",
        headers=headers,
        json={"ticker": "PETR4", "quantity": 200, "avg_price": 10.0, "category": "acoes_br"},
    )
    resp = client.post(
        "/api/portfolio/sell",
        headers=headers,
        json={"ticker": "PETR4", "quantity": 100, "sell_price": 30.0},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["ir_amount"] == 0.0


def test_loss_inside_exempt_bracket_is_not_compensable():
    cost = calculate_sell_cost(ACOES, quantity=100, sell_price=8.0, avg_price=10.0)
    assert cost.gross_profit < 0
    assert cost.loss_compensable is False
    assert "isenta" in cost.observation


def test_loss_above_exempt_bracket_is_compensable():
    cost = calculate_sell_cost(
        ACOES,
        quantity=100,
        sell_price=8.0,
        avg_price=10.0,
        gross_value_month_before=ISENCAO_MENSAL_ACOES + 1.0,
    )
    assert cost.gross_profit < 0
    assert cost.loss_compensable is True


def test_fii_loss_is_always_compensable_there_is_no_exemption():
    cost = calculate_sell_cost(FIIS, quantity=10, sell_price=80.0, avg_price=100.0)
    assert cost.loss_compensable is True


def test_non_compensable_loss_stays_out_of_the_offset_balance():
    user = "tax_offset_balance"

    portfolio_store.create_closed_trade(
        ticker="PETR4",
        category=ACOES,
        quantity=100,
        avg_price=10.0,
        sell_price=8.0,
        gross_profit=-200.0,
        ir_rate=0.0,
        ir_amount=0.0,
        net_profit=-200.0,
        loss_compensable=False,
        sold_at=time.time(),
        user_id=user,
    )
    assert portfolio_store.available_tax_loss(ACOES, user_id=user) == 0.0

    portfolio_store.create_closed_trade(
        ticker="VALE3",
        category=ACOES,
        quantity=100,
        avg_price=10.0,
        sell_price=8.0,
        gross_profit=-300.0,
        ir_rate=0.0,
        ir_amount=0.0,
        net_profit=-300.0,
        loss_compensable=True,
        sold_at=time.time(),
        user_id=user,
    )
    assert portfolio_store.available_tax_loss(ACOES, user_id=user) == 300.0


def test_offset_never_turns_ir_negative():
    cost = calculate_sell_cost(
        FIIS, quantity=10, sell_price=120.0, avg_price=100.0, accumulated_loss=999_999.0
    )
    assert cost.gross_profit == 200.0
    assert cost.ir_amount == 0.0
    assert cost.taxable_profit == 0.0
    assert cost.loss_offset_used == 200.0


def test_month_bounds_uses_brazilian_calendar_month():
    start, end = month_bounds()
    assert to_brt(start).day == 1
    assert to_brt(start).hour == 0
    assert to_brt(end).day == 1
    assert end > start


def test_month_bounds_crosses_the_year():
    december = time.mktime(time.struct_time((2026, 12, 20, 12, 0, 0, 0, 0, 0)))
    start, end = month_bounds(december)
    assert to_brt(start).month == 12
    assert to_brt(end).month == 1
    assert to_brt(end).year == to_brt(start).year + 1
