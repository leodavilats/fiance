from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from app.core.brt import month_key, now_brt
from app.core.errors import NotFoundError
from app.core.money import quantize, sum_money, to_float
from app.core.pagination import clamp_limit, paginate
from app.models.dividends import (
    DividendMonth,
    DividendReceived,
    DividendReceivedCreate,
    DividendReceivedUpdate,
    DividendsReceivedResponse,
    DividendTickerTotal,
)
from app.storage import portfolio_store


def _cents(value: Decimal) -> float:
    return to_float(quantize(value))


class DividendsService:
    def list_received(
        self,
        estimated_monthly: float | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> DividendsReceivedResponse:
        page_size = clamp_limit(limit)
        page = paginate(
            [
                self._to_model(r)
                for r in portfolio_store.list_dividends_received(limit=page_size, cursor=cursor)
            ],
            page_size,
            key=lambda i: i.paid_at.isoformat(),
            identity=lambda i: i.id,
        )

        today = now_brt().date()
        current_month = today.strftime("%Y-%m")
        cutoff_12m = today - timedelta(days=365)
        cutoff_iso = cutoff_12m.isoformat()

        amounts = portfolio_store.list_dividend_amounts()
        total = sum_money(r["amount"] for r in amounts)
        this_month = sum_money(r["amount"] for r in amounts if r["paid_at"][:7] == current_month)
        last_12m = sum_money(r["amount"] for r in amounts if r["paid_at"][:10] >= cutoff_iso)

        by_month: dict[str, list[Decimal]] = defaultdict(list)
        by_ticker: dict[str, list[Decimal]] = defaultdict(list)
        for row in amounts:
            by_month[row["paid_at"][:7]].append(row["amount"])
            by_ticker[row["ticker"]].append(row["amount"])

        months_with_data = [m for m in by_month if m >= cutoff_12m.strftime("%Y-%m")]
        monthly_average = _cents(last_12m / len(months_with_data)) if months_with_data else 0.0

        accuracy = None
        if estimated_monthly and estimated_monthly > 0 and monthly_average > 0:
            accuracy = round(monthly_average / estimated_monthly * 100, 1)

        month_totals = {m: sum_money(v) for m, v in by_month.items()}
        ticker_totals = {t: sum_money(v) for t, v in by_ticker.items()}

        return DividendsReceivedResponse(
            items=page.items,
            next_cursor=page.next_cursor,
            has_more=page.has_more,
            total_count=len(amounts),
            total_received=_cents(total),
            received_this_month=_cents(this_month),
            received_last_12m=_cents(last_12m),
            monthly_average_12m=monthly_average,
            by_month=[
                DividendMonth(month=m, total=_cents(month_totals[m]), count=len(by_month[m]))
                for m in sorted(by_month, reverse=True)
            ],
            by_ticker=[
                DividendTickerTotal(ticker=t, total=_cents(ticker_totals[t]), count=len(v))
                for t, v in sorted(by_ticker.items(), key=lambda kv: -ticker_totals[kv[0]])
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
