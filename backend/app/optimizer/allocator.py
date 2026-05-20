from __future__ import annotations

from typing import List

from app.models.recommendation import Allocation
from app.models.company import ScoredCompany

def allocate(

    ranked: List[ScoredCompany],

    cash: float,

    max_positions: int,

) -> List[Allocation]:

    candidates = [s for s in ranked if s.score > 0][:max_positions]

    if not candidates:

        return []

    total_score = sum(c.score for c in candidates)

    targets = {c.fundamentals.ticker: (c.score / total_score) * cash for c in candidates}

    allocations: List[Allocation] = []

    remaining = cash

    for c in candidates:

        f = c.fundamentals

        target_value = targets[f.ticker]

        qty = int(target_value // f.price)

        if qty <= 0:

            continue

        invested = qty * f.price

        if invested > remaining:

            qty = int(remaining // f.price)

            invested = qty * f.price

        if qty <= 0:

            continue

        remaining -= invested

        allocations.append(

            Allocation(

                ticker=f.ticker,

                name=f.name,

                sector=f.sector,

                price=round(f.price, 2),

                quantity=qty,

                invested=round(invested, 2),

                weight=0.0,

                score=c.score,

                rationale=c.rationale,

            )

        )

    changed = True

    while changed and remaining > 0:

        changed = False

        for a in allocations:

            if a.price <= remaining:

                a.quantity += 1

                a.invested = round(a.invested + a.price, 2)

                remaining -= a.price

                changed = True

                break

    invested_total = sum(a.invested for a in allocations)

    if invested_total > 0:

        for a in allocations:

            a.weight = round(a.invested / invested_total, 4)

    return allocations

