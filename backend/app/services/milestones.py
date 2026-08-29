from __future__ import annotations

import logging

from app.core.context import get_current_user_id_or_none
from app.storage import event_store

logger = logging.getLogger("fiance.milestones")

READABLE_PORTFOLIO_SIZE = 4


def _record_once(user_id: str, name: str, props: dict[str, str] | None = None) -> bool:
    if event_store.has_event(user_id, name):
        return False
    event_store.record(user_id, name, props or {}, platform="server")
    return True


def record_portfolio_milestones(position_count: int, user_id: str | None = None) -> None:
    uid = user_id or get_current_user_id_or_none()
    if not uid:
        return

    try:
        if position_count >= 1:
            primeira = _record_once(uid, "portfolio_first_position_added")
            if primeira:
                from app.services import referral_service, subscription_service

                subscription_service.start_trial(uid)
                referral_service.qualify(uid)

        if position_count >= READABLE_PORTFOLIO_SIZE:
            _record_once(uid, "portfolio_reached_4_assets")
    except Exception:
        logger.warning("Falha ao gravar marco de carteira para %s", uid, exc_info=True)
