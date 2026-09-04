from __future__ import annotations

from app.collectors.rates import get_rates
from app.collectors.universal import fetch_ibov_history
from app.core.brt import to_brt
from app.models import BenchmarkPoint, BenchmarkResponse
from app.repositories import PortfolioRepository


def _twr_series(
    snapshots: list[dict],
    realized: list[float] | None = None,
    dividends: list[float] | None = None,
) -> list[float]:
    cumulative = 1.0
    out = [0.0]
    periods = max(len(snapshots) - 1, 0)
    realized = realized or [0.0] * periods
    dividends = dividends or [0.0] * periods

    for index, (previous, current) in enumerate(zip(snapshots, snapshots[1:], strict=False)):
        opening = previous["total_current"]
        invested_delta = current["total_invested"] - previous["total_invested"]
        flow = invested_delta - (realized[index] if index < len(realized) else 0.0)
        closing = current["total_current"] + (dividends[index] if index < len(dividends) else 0.0)

        if opening <= 0:
            cumulative *= 1.0
        else:
            period_return = (closing - flow) / opening - 1
            cumulative *= 1 + period_return

        out.append(round((cumulative - 1) * 100, 4))

    return out


def _dividends_per_period(snapshots: list[dict], received: list[dict]) -> list[float]:
    periods = max(len(snapshots) - 1, 0)
    if periods == 0 or not received:
        return []

    closing_days = [_brt_day(snap["captured_at"]) for snap in snapshots[1:]]
    opening_day = _brt_day(snapshots[0]["captured_at"])

    out = [0.0] * periods
    for row in received:
        paid_at = row.get("paid_at")
        amount = float(row.get("amount") or 0.0)
        if not paid_at or amount == 0.0:
            continue
        if paid_at <= opening_day:
            continue
        for index, closing_day in enumerate(closing_days):
            if paid_at <= closing_day:
                out[index] += amount
                break

    return out


def _brt_day(timestamp: float) -> str:
    return to_brt(timestamp).strftime("%Y-%m-%d")


class BenchmarkService:
    def __init__(self):
        self.portfolio_repo = PortfolioRepository()

    async def get_benchmark(self) -> BenchmarkResponse:
        snapshots = self.portfolio_repo.list_snapshots(limit=365)

        if len(snapshots) < 2:
            return BenchmarkResponse(
                points=[], ibov_available=False, cdi_source=get_rates()["source"]
            )

        base_ts = snapshots[0]["captured_at"]

        rates = get_rates()
        cdi_daily_rate = (1 + rates["cdi_anual"] / 100) ** (1 / 365) - 1

        ibov_series = await fetch_ibov_history(days=400)
        ibov_available = bool(ibov_series)
        ibov_base = None
        if ibov_available:
            first_day = _brt_day(base_ts)
            ibov_base = ibov_series.get(first_day) or next(iter(ibov_series.values()), None)
            ibov_available = ibov_base is not None and ibov_base > 0

        realized = [
            self.portfolio_repo.realized_gross_profit_between(
                previous["captured_at"], current["captured_at"]
            )
            for previous, current in zip(snapshots, snapshots[1:], strict=False)
        ]
        dividends = _dividends_per_period(snapshots, self.portfolio_repo.list_dividends_received())
        portfolio_series = _twr_series(snapshots, realized, dividends)

        points: list[BenchmarkPoint] = []
        for snap, portfolio_pct in zip(snapshots, portfolio_series, strict=True):
            day_str = _brt_day(snap["captured_at"])
            days_elapsed = (snap["captured_at"] - base_ts) / 86400

            cdi_pct = ((1 + cdi_daily_rate) ** days_elapsed - 1) * 100

            ibov_pct = None
            if ibov_available:
                ibov_close = ibov_series.get(day_str)
                if ibov_close:
                    ibov_pct = (ibov_close / ibov_base - 1) * 100

            points.append(
                BenchmarkPoint(
                    date=day_str,
                    portfolio_pct=round(portfolio_pct, 2),
                    cdi_pct=round(cdi_pct, 2),
                    ibov_pct=round(ibov_pct, 2) if ibov_pct is not None else None,
                    invested=round(snap["total_invested"], 2),
                    patrimony=round(snap["total_current"], 2),
                )
            )

        first = snapshots[0]
        last_snap = snapshots[-1]
        net_contributions = round(last_snap["total_invested"] - first["total_invested"], 2)

        last = points[-1]
        return BenchmarkResponse(
            points=points,
            ibov_available=ibov_available,
            portfolio_return_pct=last.portfolio_pct,
            cdi_return_pct=last.cdi_pct,
            ibov_return_pct=last.ibov_pct,
            net_contributions=net_contributions,
            method="twr",
            cdi_source=rates["source"],
        )
