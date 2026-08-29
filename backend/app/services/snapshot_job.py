from __future__ import annotations

import logging

from app.core.context import reset_current_user_id, set_current_user_id
from app.models import PortfolioEvaluationRequest, PortfolioItem
from app.models.enums import AssetType
from app.storage import portfolio_store

logger = logging.getLogger("fiance.snapshot_job")


async def record_snapshot_for_user(user_id: str) -> bool:
    from app.services import FixedIncomeService, PortfolioService

    token = set_current_user_id(user_id)
    try:
        stored = portfolio_store.list_positions()
        positions = []

        if stored:
            evaluation = await PortfolioService().evaluate_portfolio(
                PortfolioEvaluationRequest(
                    items=[
                        PortfolioItem(
                            ticker=i["ticker"],
                            quantity=i["quantity"],
                            avg_price=i["avg_price"],
                            category=i.get("category", "auto"),
                        )
                        for i in stored
                    ]
                )
            )
            positions = list(evaluation.positions)

        positions += FixedIncomeService().as_portfolio_positions()

        if not positions:
            return False

        priced = [
            p
            for p in positions
            if p.current_value is not None or p.asset_type == AssetType.renda_fixa
        ]
        if not priced:
            logger.info("Snapshot de %s ignorado: nenhuma cotação disponível.", user_id)
            return False

        total_invested = sum(p.invested for p in positions)
        total_current = sum((p.current_value or p.invested) for p in positions)
        total_pnl = total_current - total_invested
        total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0

        portfolio_store.record_snapshot(
            total_invested=round(total_invested, 2),
            total_current=round(total_current, 2),
            total_pnl=round(total_pnl, 2),
            total_pnl_pct=round(total_pnl_pct, 2),
            user_id=user_id,
        )
        return True
    finally:
        reset_current_user_id(token)


async def run_snapshot_cycle() -> int:
    recorded = 0
    for user_id in portfolio_store.list_all_user_ids():
        try:
            if await record_snapshot_for_user(user_id):
                recorded += 1
        except Exception:
            logger.exception("Falha ao gravar snapshot do usuário %s", user_id)

    if recorded:
        logger.info("Snapshot diário gravado para %d usuário(s).", recorded)
    return recorded
