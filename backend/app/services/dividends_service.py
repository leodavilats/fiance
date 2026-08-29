from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from app.core.brt import month_key, now_brt
from app.core.errors import NotFoundError
from app.core.pagination import clamp_limit, slice_after
from app.models.dividends import (
    DividendMonth,
    DividendReceived,
    DividendReceivedCreate,
    DividendReceivedUpdate,
    DividendsReceivedResponse,
    DividendTickerTotal,
)
from app.storage import portfolio_store


class DividendsService:
    def list_received(
        self,
        estimated_monthly: float | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> DividendsReceivedResponse:
        rows = portfolio_store.list_dividends_received()
        items = [
            DividendReceived(
                id=r["id"],
                ticker=r["ticker"],
                paid_at=date.fromisoformat(r["paid_at"]),
                amount=r["amount"],
                kind=r["kind"],
                note=r["note"],
            )
            for r in rows
        ]

        page = slice_after(
            items,
            cursor,
            clamp_limit(limit),
            key=lambda i: i.paid_at.isoformat(),
            identity=lambda i: i.id,
        )

        today = now_brt().date()
        current_month = today.strftime("%Y-%m")
        cutoff_12m = today - timedelta(days=365)

        total = sum(i.amount for i in items)
        this_month = sum(i.amount for i in items if i.paid_at.strftime("%Y-%m") == current_month)
        last_12m = sum(i.amount for i in items if i.paid_at >= cutoff_12m)

        by_month: dict[str, list[float]] = defaultdict(list)
        by_ticker: dict[str, list[float]] = defaultdict(list)
        for item in items:
            by_month[item.paid_at.strftime("%Y-%m")].append(item.amount)
            by_ticker[item.ticker].append(item.amount)

        months_with_data = [m for m in by_month if m >= cutoff_12m.strftime("%Y-%m")]
        monthly_average = last_12m / len(months_with_data) if months_with_data else 0.0

        accuracy = None
        if estimated_monthly and estimated_monthly > 0 and monthly_average > 0:
            accuracy = round(monthly_average / estimated_monthly * 100, 1)

        return DividendsReceivedResponse(
            items=page.items,
            next_cursor=page.next_cursor,
            has_more=page.has_more,
            total_count=len(items),
            total_received=round(total, 2),
            received_this_month=round(this_month, 2),
            received_last_12m=round(last_12m, 2),
            monthly_average_12m=round(monthly_average, 2),
            by_month=[
                DividendMonth(month=m, total=round(sum(v), 2), count=len(v))
                for m, v in sorted(by_month.items(), reverse=True)
            ],
            by_ticker=[
                DividendTickerTotal(ticker=t, total=round(sum(v), 2), count=len(v))
                for t, v in sorted(by_ticker.items(), key=lambda kv: -sum(kv[1]))
            ],
            estimated_monthly=round(estimated_monthly, 2)
            if estimated_monthly is not None
            else None,
            estimate_accuracy_pct=accuracy,
        )

    def create(self, req: DividendReceivedCreate) -> DividendReceived:
        row = portfolio_store.create_dividend_received(
            ticker=req.ticker.upper(),
            paid_at=req.paid_at.isoformat(),
            amount=req.amount,
            kind=req.kind,
            note=req.note,
        )
        return self._to_model(row)

    def update(self, dividend_id: int, req: DividendReceivedUpdate) -> DividendReceived:
        fields = req.model_dump(exclude_unset=True)
        if "paid_at" in fields and fields["paid_at"] is not None:
            fields["paid_at"] = fields["paid_at"].isoformat()
        if "ticker" in fields and fields["ticker"] is not None:
            fields["ticker"] = fields["ticker"].upper()

        row = portfolio_store.update_dividend_received(dividend_id, **fields)
        if row is None:
            raise NotFoundError(f"Provento {dividend_id} não encontrado.")
        return self._to_model(row)

    def delete(self, dividend_id: int) -> dict:
        if not portfolio_store.delete_dividend_received(dividend_id):
            raise NotFoundError(f"Provento {dividend_id} não encontrado.")
        return {"deleted": dividend_id}

    def received_this_month(self) -> float:
        current = now_brt().strftime("%Y-%m")
        return round(
            sum(
                r["amount"]
                for r in portfolio_store.list_dividends_received()
                if r["paid_at"][:7] == current
            ),
            2,
        )

    def monthly_totals(self) -> dict[str, float]:
        totals: dict[str, float] = defaultdict(float)
        for row in portfolio_store.list_dividends_received():
            totals[row["paid_at"][:7]] += row["amount"]
        return dict(totals)

    @staticmethod
    def _to_model(row: dict) -> DividendReceived:
        return DividendReceived(
            id=row["id"],
            ticker=row["ticker"],
            paid_at=date.fromisoformat(row["paid_at"]),
            amount=row["amount"],
            kind=row["kind"],
            note=row["note"],
        )


__all__ = ["DividendsService", "month_key"]
