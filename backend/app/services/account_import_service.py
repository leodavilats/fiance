from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from pydantic import ValidationError

from app.cashflow import CashEntry, CashKind
from app.cashflow.debt import Debt
from app.core.brt import BRT
from app.core.errors import ConflictError, DomainError
from app.ledger import LedgerEntry, TransactionKind
from app.models.alerts import MAX_ALERTS_PER_USER, AlertCreate
from app.models.dividends import DividendReceivedCreate
from app.models.followed import FollowedSuggestionCreate
from app.models.goal import Goal, SectorGoal
from app.models.preferences import PreferencesRequest
from app.models.renda_fixa import FixedIncomeCreateRequest
from app.services import cashflow_service, ledger_service
from app.services.fixed_income_service import FixedIncomeService
from app.services.milestones import record_holdings_milestones
from app.storage import cash_store, ledger_store, portfolio_store

FORMAT_VERSION = 1

SECTIONS = {
    "transactions": "Lançamentos do razão",
    "positions": "Posições sem lançamento, que entram como declaração",
    "fixed_income_positions": "Renda fixa",
    "dividends_received": "Proventos recebidos",
    "followed_suggestions": "Sugestões seguidas",
    "cash_entries": "Lançamentos do mês",
    "debts": "Dívidas",
    "goals": "Metas de alocação",
    "sector_goals": "Metas por setor",
    "preferences": "Preferências",
    "price_alerts": "Alertas de preço",
    "snapshots": "Histórico do patrimônio",
}

LEFT_OUT = {
    "notified_opportunities": "avisos já enviados",
    "device_tokens": "aparelhos cadastrados para notificação",
    "audit_log": "registro de atividade",
    "subscription": "assinatura",
    "checkout_sessions": "sessões de pagamento",
    "product_events": "eventos de uso",
    "referral_code": "código de indicação",
    "referrals_made": "indicações feitas",
    "cash_recurrences": "recorrências de caixa",
}


class ImportRejected(DomainError):
    status_code = 422


@dataclass
class _Plan:
    exported_at: float | None = None
    source_email: str | None = None
    entries: list[tuple[int | None, LedgerEntry]] = field(default_factory=list)
    declared: list[LedgerEntry] = field(default_factory=list)
    categories: dict[str, str] = field(default_factory=dict)
    fixed_income: list[FixedIncomeCreateRequest] = field(default_factory=list)
    dividends: list[DividendReceivedCreate] = field(default_factory=list)
    followed: list[tuple[int | None, dict]] = field(default_factory=list)
    cash: list[CashEntry] = field(default_factory=list)
    debts: list[tuple[Debt, bool]] = field(default_factory=list)
    goals: list[Goal] | None = None
    sector_goals: list[SectorGoal] | None = None
    preferences: dict | None = None
    alerts: list[AlertCreate] = field(default_factory=list)
    snapshots: list[dict] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        return {
            "transactions": len(self.entries),
            "positions": len(self.declared),
            "fixed_income_positions": len(self.fixed_income),
            "dividends_received": len(self.dividends),
            "followed_suggestions": len(self.followed),
            "cash_entries": len(self.cash),
            "debts": len(self.debts),
            "goals": len(self.goals or []),
            "sector_goals": len(self.sector_goals or []),
            "preferences": 1 if self.preferences else 0,
            "price_alerts": len(self.alerts),
            "snapshots": len(self.snapshots),
        }


def _number(value) -> float:
    return float(str(value))


def _day(timestamp: float | None) -> str:
    moment = datetime.fromtimestamp(timestamp, BRT) if timestamp else datetime.now(BRT)
    return moment.date().isoformat()


def _message(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        erro = exc.errors()[0]
        campo = ".".join(str(p) for p in erro.get("loc", ()))
        return f"{campo}: {erro.get('msg')}" if campo else str(erro.get("msg"))
    return str(exc)


def _read(payload: dict) -> _Plan:
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
        raise ImportRejected("O arquivo não é uma exportação do fiance: falta o bloco de dados.")
    if payload.get("format_version") != FORMAT_VERSION:
        raise ImportRejected(
            f"Formato {payload.get('format_version')!r} desconhecido: esta versão lê o formato "
            f"{FORMAT_VERSION}."
        )

    data = payload["data"]
    plan = _Plan(
        exported_at=payload.get("exported_at"),
        source_email=(payload.get("user") or {}).get("email"),
    )

    def rows(section: str) -> list[dict]:
        valor = data.get(section) or []
        return [r for r in valor if isinstance(r, dict)] if isinstance(valor, list) else []

    def each(section: str, build) -> None:
        for index, row in enumerate(rows(section), start=1):
            try:
                build(row)
            except (DomainError, ValueError, TypeError, KeyError, ValidationError) as exc:
                plan.issues.append(
                    {
                        "section": section,
                        "label": SECTIONS.get(section, section),
                        "index": index,
                        "message": _message(exc),
                    }
                )

    def entry(row: dict) -> None:
        plan.entries.append(
            (
                row.get("id"),
                LedgerEntry(
                    kind=TransactionKind(row["kind"]),
                    symbol=row["symbol"],
                    traded_on=row["traded_on"],
                    quantity=_number(row.get("quantity") or 0),
                    price=_number(row.get("price") or 0),
                    fees=_number(row.get("fees") or 0),
                    ratio_from=_number(row.get("ratio_from") or 1),
                    ratio_to=_number(row.get("ratio_to") or 1),
                    amount=_number(row.get("amount") or 0),
                    note=row.get("note"),
                ),
            )
        )

    each("transactions", entry)
    no_razao = {e.symbol.strip().upper() for _, e in plan.entries}

    def position(row: dict) -> None:
        ticker = str(row["ticker"]).strip().upper()
        category = row.get("category") or "auto"
        if category != "auto":
            plan.categories[ticker] = category
        if ticker in no_razao:
            return
        plan.declared.append(
            LedgerEntry(
                kind=TransactionKind.ADJUST,
                symbol=ticker,
                traded_on=_day(plan.exported_at),
                quantity=_number(row["quantity"]),
                price=_number(row["avg_price"]),
                note="Posição trazida da exportação da conta.",
            )
        )

    each("positions", position)

    def fixed_income(row: dict) -> None:
        campos = {k: row[k] for k in FixedIncomeCreateRequest.model_fields if k in row}
        campos["valor_investido"] = _number(row["valor_investido"])
        campos["oculto"] = bool(row.get("oculto"))
        plan.fixed_income.append(FixedIncomeCreateRequest(**campos))

    each("fixed_income_positions", fixed_income)
    each(
        "dividends_received",
        lambda row: plan.dividends.append(
            DividendReceivedCreate(
                ticker=row["ticker"],
                paid_at=row["paid_at"],
                amount=_number(row["amount"]),
                kind=row.get("kind") or "dividendo",
                note=row.get("note"),
            )
        ),
    )

    def followed(row: dict) -> None:
        campos = FollowedSuggestionCreate(
            ticker=row["ticker"],
            source=row.get("source") or "opportunities",
            action=row.get("action") or "comprar",
            quantity=_number(row["quantity"]),
            price=_number(row["price"]),
            followed_on=row["followed_on"],
            score_at_suggestion=row.get("score_at_suggestion"),
            verdict_at_suggestion=row.get("verdict_at_suggestion"),
            note=row.get("note"),
        )
        plan.followed.append((row.get("ledger_entry_id"), campos.model_dump()))

    each("followed_suggestions", followed)

    each(
        "cash_entries",
        lambda row: plan.cash.append(
            CashEntry(
                kind=CashKind(row["kind"]),
                category=row["category"],
                description=row["description"],
                amount=_number(row["amount"]),
                due_on=row["due_on"],
                paid_on=row.get("paid_on"),
            )
        ),
    )
    each(
        "debts",
        lambda row: plan.debts.append(
            (
                Debt(
                    kind=row["kind"],
                    description=row["description"],
                    balance=_number(row["balance"]),
                    monthly_rate=row.get("monthly_rate"),
                ),
                row.get("settled_at") is not None,
            )
        ),
    )

    if "goals" in data:
        plan.goals = []
        each(
            "goals",
            lambda row: plan.goals.append(
                Goal(
                    category=row["category"],
                    target_pct=row["target_pct"],
                    target_value=(
                        _number(row["target_value"]) if row.get("target_value") else None
                    ),
                    deadline=row.get("deadline"),
                )
            ),
        )
    if "sector_goals" in data:
        plan.sector_goals = []
        each(
            "sector_goals",
            lambda row: plan.sector_goals.append(
                SectorGoal(sector=row["sector"], target_pct=row["target_pct"])
            ),
        )

    def preferences(row: dict) -> None:
        campos = {k: row[k] for k in PreferencesRequest.model_fields if k in row}
        for lista in ("preferred_categories", "preferred_sectors", "excluded_tickers"):
            if isinstance(campos.get(lista), str):
                campos[lista] = [p for p in campos[lista].split(",") if p]
        for dinheiro in ("cash_available", "passive_income_goal"):
            if campos.get(dinheiro) is not None:
                campos[dinheiro] = _number(campos[dinheiro])
        plan.preferences = PreferencesRequest(**campos).model_dump(exclude_unset=True, mode="json")

    each("preferences", preferences)

    def alert(row: dict) -> None:
        if row.get("triggered_at") is not None:
            return
        plan.alerts.append(
            AlertCreate(
                ticker=row["ticker"],
                condition=row["condition"],
                target_price=_number(row["target_price"]),
                note=row.get("note"),
            )
        )

    each("price_alerts", alert)
    plan.alerts = plan.alerts[:MAX_ALERTS_PER_USER]

    each(
        "snapshots",
        lambda row: plan.snapshots.append(
            {
                "captured_at": float(row["captured_at"]),
                "total_invested": _number(row["total_invested"]),
                "total_current": _number(row["total_current"]),
                "total_pnl": _number(row["total_pnl"]),
                "total_pnl_pct": float(row["total_pnl_pct"]),
            }
        ),
    )
    return plan


def _what_the_account_has(user_id: str) -> list[str]:
    tem = []
    if ledger_store.list_entries(user_id=user_id, limit=1):
        tem.append("lançamentos no razão")
    if portfolio_store.has_holdings(user_id):
        tem.append("posições ou renda fixa")
    if portfolio_store.list_dividends_received(user_id=user_id, limit=1):
        tem.append("proventos recebidos")
    if cash_store.list_entries(user_id=user_id):
        tem.append("lançamentos do mês")
    if cash_store.list_debts(user_id=user_id, include_settled=True):
        tem.append("dívidas")
    if portfolio_store.list_followed_suggestions(user_id=user_id, limit=1):
        tem.append("sugestões seguidas")
    return tem


def preview(payload: dict, user_id: str) -> dict:
    plan = _read(payload)
    counts = plan.counts()
    blockers = _what_the_account_has(user_id)
    return {
        "format_version": FORMAT_VERSION,
        "exported_at": plan.exported_at,
        "source_email": plan.source_email,
        "sections": [
            {"section": s, "label": label, "count": counts[s]}
            for s, label in SECTIONS.items()
            if counts[s]
        ],
        "left_out": [
            {"section": s, "label": label}
            for s, label in LEFT_OUT.items()
            if (payload.get("data") or {}).get(s)
        ],
        "issues": plan.issues,
        "blockers": blockers,
        "ok": not plan.issues and not blockers and any(counts.values()),
    }


def apply(payload: dict, user_id: str) -> dict:
    plan = _read(payload)
    if plan.issues:
        primeiros = "; ".join(
            f"{i['label']}, item {i['index']}: {i['message']}" for i in plan.issues[:3]
        )
        raise ImportRejected(
            f"{len(plan.issues)} item(ns) com problema no arquivo, e nada foi gravado: {primeiros}"
        )
    blockers = _what_the_account_has(user_id)
    if blockers:
        raise ConflictError(
            "A importação só entra em conta sem dados financeiros, para não somar o arquivo ao que "
            f"já existe. Esta conta tem: {', '.join(blockers)}."
        )

    if plan.preferences:
        portfolio_store.set_preferences(user_id=user_id, **plan.preferences)
    if plan.goals:
        portfolio_store.replace_goals([g.model_dump() for g in plan.goals], user_id=user_id)
    if plan.sector_goals:
        portfolio_store.replace_sector_goals(
            [g.model_dump() for g in plan.sector_goals], user_id=user_id
        )

    ordenadas = sorted(plan.entries, key=lambda par: (par[1].traded_on, par[0] or 0))
    novos = ledger_service.import_entries(
        [e for _, e in ordenadas] + plan.declared, user_id=user_id
    )
    de_para = {
        antigo: novo
        for (antigo, _), novo in zip(ordenadas, novos, strict=False)
        if antigo is not None
    }
    for ticker, category in plan.categories.items():
        ledger_service.rebuild_projection(symbol=ticker, category=category, user_id=user_id)

    for req in plan.fixed_income:
        portfolio_store.create_fixed_income(
            user_id=user_id, **FixedIncomeService._to_storage(req.model_dump())
        )
    for req in plan.dividends:
        portfolio_store.create_dividend_received(
            user_id=user_id,
            ticker=req.ticker.upper(),
            paid_at=req.paid_at.isoformat(),
            amount=req.amount,
            kind=req.kind,
            note=req.note,
        )
    for antigo, campos in plan.followed:
        portfolio_store.create_followed_suggestion(
            user_id=user_id,
            ticker=campos["ticker"].upper(),
            source=campos["source"],
            action=campos["action"],
            quantity=campos["quantity"],
            price=campos["price"],
            followed_on=campos["followed_on"].isoformat(),
            score_at_suggestion=campos["score_at_suggestion"],
            verdict_at_suggestion=campos["verdict_at_suggestion"],
            note=campos["note"],
            ledger_entry_id=de_para.get(antigo) if antigo is not None else None,
        )
    for debt, quitada in plan.debts:
        debt_id = cashflow_service.cadastrar_divida(debt, user_id=user_id)
        if quitada:
            cashflow_service.quitar_divida(debt_id, user_id=user_id)
    if plan.cash:
        cashflow_service.registrar_varias(plan.cash, user_id=user_id)
    for alerta in plan.alerts:
        portfolio_store.create_price_alert(
            ticker=alerta.ticker,
            condition=alerta.condition,
            target_price=alerta.target_price,
            note=alerta.note,
            user_id=user_id,
        )
    for snapshot in plan.snapshots:
        portfolio_store.restore_snapshot(user_id=user_id, **snapshot)

    record_holdings_milestones(user_id=user_id)
    return {"imported": plan.counts()}
