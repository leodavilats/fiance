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


def test_dividend_does_not_look_like_a_loss():
    """No ex-dividendo o preço cai; o dinheiro pago não está em `total_current`.

    Sem contar o provento como valor distribuído, a carteira apareceria
    perdendo exatamente o que ganhou.
    """
    snapshots = [_snap(1000, 1000, 0), _snap(1000, 950, 1)]

    sem_provento = _twr_series(snapshots)
    com_provento = _twr_series(snapshots, realized=[0.0], dividends=[50.0])

    assert sem_provento[-1] == -5.0
    assert com_provento[-1] == 0.0


def test_dividend_is_return_not_contribution():
    snapshots = [_snap(1000, 1000, 0), _snap(1000, 1000, 1)]

    assert _twr_series(snapshots, dividends=[100.0])[-1] == 10.0


def test_convencao_de_borda_do_provento_e_pelo_dia_de_fechamento():
    """`paid_at` é dia; `captured_at` é instante. A borda precisa ser escrita."""
    from app.services.benchmark_service import _dividends_per_period

    # Snapshots em 2026-08-25, 2026-08-27 e 2026-08-29 (fuso brasileiro).
    def em(dia: str, invested: float = 1000.0) -> dict:
        from datetime import datetime

        from app.core.brt import BRT

        moment = datetime.fromisoformat(f"{dia}T22:00:00").replace(tzinfo=BRT)
        return {
            "captured_at": moment.timestamp(),
            "total_invested": invested,
            "total_current": invested,
        }

    snapshots = [em("2026-08-25"), em("2026-08-27"), em("2026-08-29")]
    recebidos = [
        {"paid_at": "2026-08-26", "amount": 10.0},
        {"paid_at": "2026-08-27", "amount": 20.0},
        {"paid_at": "2026-08-28", "amount": 5.0},
        {"paid_at": "2026-08-20", "amount": 99.0},
    ]

    por_periodo = _dividends_per_period(snapshots, recebidos)

    assert por_periodo == [30.0, 5.0], (
        "pago no dia do fechamento entra nesse período; anterior ao início fica de fora"
    )


def test_dia_do_benchmark_e_o_dia_brasileiro():
    """Às 22h de Brasília o UTC já virou — e o fechamento do Ibov some."""
    from datetime import datetime

    from app.core.brt import BRT
    from app.services.benchmark_service import _brt_day

    noite = datetime(2026, 8, 27, 22, 30, tzinfo=BRT).timestamp()

    assert _brt_day(noite) == "2026-08-27"
