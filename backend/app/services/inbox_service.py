from __future__ import annotations

from datetime import date

from app.analysis.texto import reais
from app.core.brt import now_brt
from app.core.context import reset_current_user_id, set_current_user_id
from app.core.pagination import clamp_limit, paginate
from app.models.whats_new import WhatsNewItem
from app.storage import inbox_store
from app.storage.inbox_store import InboxNotice

_SEMANAL = frozenset({"patrimony", "new_opportunity"})
_MENSAL = frozenset({"verdict_change", "allocation", "tax"})

INBOX_PAGE_SIZE = 30


def _periodo(kind: str, hoje: date) -> str:
    if kind in _SEMANAL:
        ano, semana, _ = hoje.isocalendar()
        return f"{ano}-S{semana:02d}"
    if kind in _MENSAL:
        return hoje.strftime("%Y-%m")
    return ""


def notices_from_whats_new(items: list[WhatsNewItem], hoje: date) -> list[InboxNotice]:
    return [
        InboxNotice(
            dedup_key=f"{item.topic}@{_periodo(item.kind, hoje)}",
            kind=item.kind,
            severity=item.severity,
            title=item.title,
            detail=item.detail,
            ticker=item.ticker,
            action=item.action,
            action_label=item.action_label,
        )
        for item in items
        if item.kind != "empty" and item.topic
    ]


def price_alert_notice(alert: dict, price: float) -> InboxNotice:
    direcao = "abaixo de" if alert["condition"] == "below" else "acima de"
    return InboxNotice(
        dedup_key=f"price_alert:{alert['id']}",
        kind="price_alert",
        severity="warning",
        title=f"{alert['ticker']} está {direcao} {reais(alert['target_price'])}",
        detail=f"O preço chegou a {reais(price)}, e o alerta que você criou disparou.",
        ticker=alert["ticker"],
        action="analyze",
        action_label=f"Ver {alert['ticker']}",
    )


def digest_notice(body: str, hoje: date) -> InboxNotice:
    return InboxNotice(
        dedup_key=f"digest@{hoje.isoformat()}",
        kind="digest",
        severity="info",
        title="Resumo de oportunidades",
        detail=body,
        action="market",
        action_label="Ver oportunidades",
    )


async def sync() -> int:
    from app.services.whats_new_service import WhatsNewService

    resposta = await WhatsNewService().build()
    return inbox_store.record(notices_from_whats_new(resposta.items, now_brt().date()))


async def sync_for_user(user_id: str) -> int:
    token = set_current_user_id(user_id)
    try:
        return await sync()
    finally:
        reset_current_user_id(token)


def page(limit: int | None, cursor: str | None, kinds: list[str] | None) -> dict:
    tamanho = clamp_limit(limit or INBOX_PAGE_SIZE)
    linhas = inbox_store.list_items(tamanho, cursor, kinds)
    pagina = paginate(linhas, tamanho, key=lambda r: r["created_at"], identity=lambda r: r["id"])
    return {
        "items": pagina.items,
        "unread": inbox_store.unread_count(),
        "next_cursor": pagina.next_cursor,
        "has_more": pagina.has_more,
    }
