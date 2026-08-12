from __future__ import annotations

import logging

from app.collectors.universal import fetch_many
from app.notifications import send_push
from app.services.opportunity_service import OpportunityService
from app.storage import portfolio_store

logger = logging.getLogger("fianceai.notification_job")


async def _check_price_alerts(user_id: str, tokens: list[str]) -> None:
    alerts = [
        a for a in portfolio_store.list_price_alerts(user_id=user_id) if a["triggered_at"] is None
    ]
    if not alerts:
        return

    tickers = list({a["ticker"] for a in alerts})
    snapshots = await fetch_many(tickers)
    price_map = {s.symbol.upper(): s.price for s in snapshots if s.price is not None}

    for alert in alerts:
        price = price_map.get(alert["ticker"].upper())
        if price is None:
            continue
        hit = (alert["condition"] == "below" and price <= alert["target_price"]) or (
            alert["condition"] == "above" and price >= alert["target_price"]
        )
        if not hit:
            continue

        direction = "abaixo de" if alert["condition"] == "below" else "acima de"
        invalid = send_push(
            tokens,
            title=f"Alerta de preço: {alert['ticker']}",
            body=(
                f"{alert['ticker']} está {direction} R$ {alert['target_price']:.2f} "
                f"(atual: R$ {price:.2f})"
            ),
            data={"type": "price_alert", "ticker": alert["ticker"]},
        )
        portfolio_store.mark_alert_triggered(alert["id"], user_id=user_id)
        for invalid_token in invalid:
            portfolio_store.unregister_device_token(invalid_token, user_id=user_id)


async def _check_new_opportunities(
    user_id: str,
    tokens: list[str],
    service: OpportunityService,
    prefs: dict,
) -> None:
    scanned, _universe_size = await service._scan_universe(prefs)  # noqa: SLF001 — reuso interno

    interesting = [
        o
        for o in scanned
        if o.verdict == "STRONG_BUY" or (o.score >= 75 and (o.dividend_yield or 0) >= 6.0)
    ]
    if not interesting:
        return

    already_notified = portfolio_store.get_notified_opportunity_tickers(user_id)
    new_ones = [o for o in interesting if o.ticker.upper() not in already_notified]
    if not new_ones:
        return

    to_notify = new_ones[:3]
    for opp in to_notify:
        invalid = send_push(
            tokens,
            title=f"Nova oportunidade: {opp.ticker}",
            body=f"{opp.label} — score {opp.score:.0f}, DY {opp.dividend_yield or 0:.1f}%",
            data={"type": "new_opportunity", "ticker": opp.ticker},
        )
        for invalid_token in invalid:
            portfolio_store.unregister_device_token(invalid_token, user_id=user_id)

    portfolio_store.mark_opportunities_notified(user_id, [o.ticker.upper() for o in new_ones])


async def run_notification_cycle() -> None:
    tokens_by_user: dict[str, list[str]] = {}
    for row in portfolio_store.list_all_device_tokens():
        tokens_by_user.setdefault(row["user_id"], []).append(row["token"])

    if not tokens_by_user:
        return

    opportunity_service = OpportunityService()

    for user_id, tokens in tokens_by_user.items():
        try:
            prefs = portfolio_store.get_preferences(user_id=user_id)

            if prefs.get("notify_price_alerts", True):
                await _check_price_alerts(user_id, tokens)

            if prefs.get("notify_new_opportunities", True):
                await _check_new_opportunities(user_id, tokens, opportunity_service, prefs)
        except Exception:
            logger.exception("Falha no ciclo de notificações do usuário %s", user_id)
