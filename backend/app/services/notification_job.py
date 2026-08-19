from __future__ import annotations

import logging
import time

from app.collectors.universal import fetch_many
from app.notifications import send_push
from app.services.opportunity_service import OpportunityService
from app.storage import portfolio_store

logger = logging.getLogger("fiance.notification_job")

# Plataforma é para investimento, não day trade — cadência mínima é diária.
# Intervalos um pouco menores que o período nominal absorvem o drift do ciclo de 15 min.
_FREQUENCY_SECONDS = {
    "daily": 20 * 3600,
    "weekly": 6 * 24 * 3600,
    "monthly": 27 * 24 * 3600,
}


def _digest_due(frequency: str, last_sent_at: float | None) -> bool:
    interval = _FREQUENCY_SECONDS.get(frequency)
    if interval is None:  # "off" ou valor desconhecido
        return False
    if last_sent_at is None:
        return True
    return (time.time() - last_sent_at) >= interval


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


async def _send_opportunities_digest(
    user_id: str,
    tokens: list[str],
    service: OpportunityService,
    prefs: dict,
) -> None:
    scanned, _universe_size = await service._scan_universe(prefs)  # noqa: SLF001 — reuso interno

    excluded = {t.upper() for t in prefs.get("excluded_tickers", [])}
    by_ticker = {o.ticker.upper(): o for o in scanned}

    held_tickers = {p["ticker"].upper() for p in portfolio_store.list_positions(user_id=user_id)}
    to_review = sorted(
        (
            by_ticker[t]
            for t in held_tickers
            if t in by_ticker and by_ticker[t].verdict in ("SELL", "STRONG_SELL")
        ),
        key=lambda o: o.score,
    )[:3]

    interesting = [
        o
        for o in scanned
        if o.ticker.upper() not in held_tickers
        and o.ticker.upper() not in excluded
        and (o.verdict == "STRONG_BUY" or (o.score >= 75 and (o.dividend_yield or 0) >= 6.0))
    ]

    if not interesting and not to_review:
        return

    already_notified = portfolio_store.get_notified_opportunity_tickers(user_id)
    new_ones = [o for o in interesting if o.ticker.upper() not in already_notified]
    # Se nada é literalmente novo desde o último resumo, ainda reforça as melhores atuais —
    # o objetivo é um resumo periódico, não só alertar sobre estreias no ranking.
    highlighted = sorted(new_ones or interesting, key=lambda o: o.score, reverse=True)[:5]

    body_parts = []
    if highlighted:
        summary = ", ".join(f"{o.ticker} ({o.score:.0f})" for o in highlighted)
        body_parts.append(f"{len(interesting)} ativo(s) bem avaliados: {summary}")
    if to_review:
        review_summary = ", ".join(o.ticker for o in to_review)
        body_parts.append(f"revisar na carteira: {review_summary}")

    invalid = send_push(
        tokens,
        title="Resumo de ajuste de carteira",
        body=" · ".join(body_parts),
        data={
            "type": "opportunities_digest",
            "tickers": ",".join(o.ticker for o in highlighted),
            "review_tickers": ",".join(o.ticker for o in to_review),
        },
    )
    for invalid_token in invalid:
        portfolio_store.unregister_device_token(invalid_token, user_id=user_id)

    if highlighted:
        portfolio_store.mark_opportunities_notified(
            user_id, [o.ticker.upper() for o in highlighted]
        )


async def run_notification_cycle() -> None:
    tokens_by_user: dict[str, list[str]] = {}
    for row in portfolio_store.list_all_device_tokens():
        tokens_by_user.setdefault(row["user_id"], []).append(row["token"])

    if not tokens_by_user:
        return

    opportunity_service = OpportunityService()
    now = time.time()

    for user_id, tokens in tokens_by_user.items():
        try:
            prefs = portfolio_store.get_preferences(user_id=user_id)

            if prefs.get("notify_price_alerts", True):
                await _check_price_alerts(user_id, tokens)

            frequency = prefs.get("opportunities_frequency", "weekly")
            last_sent = portfolio_store.get_last_digest_sent_at(user_id=user_id)
            if _digest_due(frequency, last_sent):
                await _send_opportunities_digest(user_id, tokens, opportunity_service, prefs)
                portfolio_store.mark_digest_sent(now, user_id=user_id)
        except Exception:
            logger.exception("Falha no ciclo de notificações do usuário %s", user_id)
