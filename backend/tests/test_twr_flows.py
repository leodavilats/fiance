"""TWR: o fluxo externo de uma venda é o valor recebido, não o custo baixado."""

from app.services.benchmark_service import _twr_series


def _snap(invested: float, current: float, day: int) -> dict:
    return {
        "captured_at": float(day) * 86400,
        "total_invested": invested,
        "total_current": current,
        "total_pnl": current - invested,
        "total_pnl_pct": 0.0,
    }


def test_market_move_without_flow_is_the_plain_return():
    series = _twr_series([_snap(1000, 1000, 0), _snap(1000, 1100, 1)])
    assert series == [0.0, 10.0]


def test_contribution_is_not_counted_as_return():
    series = _twr_series([_snap(1000, 1000, 0), _snap(1500, 1500, 1)], realized=[0.0])
    assert series[-1] == 0.0


def test_profitable_sale_does_not_destroy_the_accumulated_return():
    snapshots = [
        _snap(1000, 1000, 0),
        _snap(1000, 1100, 1),
        _snap(500, 550, 2),
    ]
    realized = [0.0, 50.0]

    series = _twr_series(snapshots, realized)
    assert series[1] == 10.0
    assert abs(series[2] - 10.0) < 1e-6

    naive = _twr_series(snapshots)
    assert naive[2] < 10.0, "sem a correção o teste não distingue nada"


def test_sale_at_a_loss_does_not_inflate_the_return():
    snapshots = [
        _snap(1000, 1000, 0),
        _snap(1000, 900, 1),
        _snap(500, 450, 2),
    ]
    realized = [0.0, -50.0]

    series = _twr_series(snapshots, realized)
    assert abs(series[1] - (-10.0)) < 1e-6
    assert abs(series[2] - (-10.0)) < 1e-6


def test_empty_opening_value_does_not_divide_by_zero():
    series = _twr_series([_snap(0, 0, 0), _snap(1000, 1000, 1)], realized=[0.0])
    assert series == [0.0, 0.0]
