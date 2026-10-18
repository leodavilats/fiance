from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.analysis.texto import numero
from app.core.errors import DomainError
from app.core.pregao import deslocar_pregoes
from app.importing.b3 import (
    CICLO_DE_LIQUIDACAO,
    FORMATO,
    B3Dividend,
    B3Operation,
    ParsedB3,
    parse_b3_movimentacao,
)
from app.importing.parser import ImportIssue
from app.ledger import LedgerEntry, LedgerError, TransactionKind, project_position
from app.models.dividends import DividendReceivedCreate
from app.services import ledger_service
from app.services.dividends_service import DividendsService
from app.storage import ledger_store, portfolio_store

PRICE_TOLERANCE = 0.02

_PREGAO = frozenset({TransactionKind.BUY, TransactionKind.SELL})


class B3ImportRejected(DomainError):
    status_code = 422


@dataclass
class _Lida:
    parsed: ParsedB3
    operation_pairs: dict[int, LedgerEntry]
    dividend_pairs: dict[int, dict]
    issues: list[ImportIssue]
    warnings: list[ImportIssue]


def _br(dia: str) -> str:
    return date.fromisoformat(dia).strftime("%d/%m/%Y")


def _qtd(valor: float) -> str:
    return numero(valor, 0) if float(valor).is_integer() else numero(valor, 4)


def _par_de_operacao(
    operation: B3Operation, existentes: list[LedgerEntry], usados: set[int]
) -> LedgerEntry | None:
    entry = operation.entry
    pregao = date.fromisoformat(entry.traded_on)
    inicio = deslocar_pregoes(pregao, -CICLO_DE_LIQUIDACAO).isoformat()
    fim = operation.settled_on

    candidatos = [
        e
        for e in existentes
        if e.id not in usados
        and e.kind is entry.kind
        and e.symbol == entry.symbol
        and abs(e.quantity - entry.quantity) < 1e-6
        and inicio <= e.traded_on <= fim
        and abs(e.price - entry.price) <= entry.price * PRICE_TOLERANCE
    ]
    if not candidatos:
        return None
    return min(
        candidatos,
        key=lambda e: (
            abs((date.fromisoformat(e.traded_on) - pregao).days),
            abs(e.price - entry.price),
        ),
    )


def _par_de_provento(dividend: B3Dividend, existentes: list[dict], usados: set[int]) -> dict | None:
    candidatos = [
        d
        for d in existentes
        if d["id"] not in usados
        and d["ticker"] == dividend.ticker
        and d["paid_at"][:10] == dividend.paid_at
    ]
    if not candidatos:
        return None
    return min(
        candidatos,
        key=lambda d: (d["kind"] != dividend.kind, abs(float(d["amount"]) - dividend.amount)),
    )


def _liquidacao(entry: LedgerEntry) -> str:
    if entry.kind not in _PREGAO:
        return entry.traded_on
    return deslocar_pregoes(date.fromisoformat(entry.traded_on), CICLO_DE_LIQUIDACAO).isoformat()


def _conferir(
    parsed: ParsedB3,
    existentes: list[LedgerEntry],
    selecionadas: list[B3Operation],
) -> tuple[list[ImportIssue], list[ImportIssue]]:
    issues: list[ImportIssue] = []
    warnings: list[ImportIssue] = []
    novas = [op.entry for op in selecionadas]
    todas = existentes + novas

    for symbol in sorted({op.entry.symbol for op in selecionadas}):
        do_ativo = [e for e in todas if e.symbol == symbol]
        try:
            project_position(do_ativo, symbol)
        except LedgerError as exc:
            vendas = [
                op.line
                for op in selecionadas
                if op.entry.symbol == symbol and op.entry.kind is TransactionKind.SELL
            ]
            issues.append(
                ImportIssue(
                    line=min(vendas, default=0),
                    message=(
                        f"{exc} Lance antes a compra que falta, ou declare a posição de "
                        f"{symbol}, e importe de novo."
                    ),
                )
            )

    for custodia in parsed.custody:
        ate_o_dia = [
            e for e in todas if e.symbol == custodia.symbol and _liquidacao(e) <= custodia.on
        ]
        try:
            no_razao = project_position(ate_o_dia, custodia.symbol).quantity
        except LedgerError:
            continue
        if abs(no_razao - custodia.quantity) > 1e-6:
            warnings.append(
                ImportIssue(
                    line=custodia.line,
                    message=(
                        f"A B3 tinha {_qtd(custodia.quantity)} {custodia.symbol} em "
                        f"{_br(custodia.on)}; com esta importação, o razão teria "
                        f"{_qtd(no_razao)} nessa data."
                    ),
                )
            )

    return issues, warnings


def _ler(conteudo: bytes, incluir: set[int] | None) -> _Lida:
    parsed = parse_b3_movimentacao(conteudo)
    existentes = ledger_store.list_entries()

    operation_pairs: dict[int, LedgerEntry] = {}
    usados: set[int] = set()
    for op in parsed.operations:
        par = _par_de_operacao(op, existentes, usados)
        if par is not None and par.id is not None:
            operation_pairs[op.line] = par
            usados.add(par.id)

    dividend_pairs: dict[int, dict] = {}
    proventos = portfolio_store.list_dividends_received()
    usados = set()
    for dividend in parsed.dividends:
        par = _par_de_provento(dividend, proventos, usados)
        if par is not None:
            dividend_pairs[dividend.line] = par
            usados.add(par["id"])

    incluir = incluir or set()
    selecionadas = [
        op for op in parsed.operations if op.line not in operation_pairs or op.line in incluir
    ]
    issues, warnings = ([], []) if parsed.issues else _conferir(parsed, existentes, selecionadas)

    return _Lida(
        parsed=parsed,
        operation_pairs=operation_pairs,
        dividend_pairs=dividend_pairs,
        issues=sorted(parsed.issues + issues, key=lambda i: i.line),
        warnings=sorted(parsed.warnings + warnings, key=lambda i: i.line),
    )


def _par_out_operacao(entry: LedgerEntry) -> dict:
    return {
        "id": entry.id,
        "day": entry.traded_on,
        "quantity": entry.quantity,
        "price": entry.price,
        "amount": None,
    }


def _par_out_provento(row: dict) -> dict:
    return {
        "id": row["id"],
        "day": row["paid_at"][:10],
        "quantity": None,
        "price": None,
        "amount": float(row["amount"]),
    }


def preview(conteudo: bytes) -> dict:
    lida = _ler(conteudo, None)

    rows = [
        {
            "line": op.line,
            "target": "operacao",
            "kind": op.entry.kind.value,
            "symbol": op.entry.symbol,
            "day": op.entry.traded_on,
            "settled_on": op.settled_on,
            "quantity": op.entry.quantity,
            "price": op.entry.price,
            "amount": round(op.entry.quantity * op.entry.price, 2),
            "duplicate": _par_out_operacao(lida.operation_pairs[op.line])
            if op.line in lida.operation_pairs
            else None,
        }
        for op in lida.parsed.operations
    ] + [
        {
            "line": d.line,
            "target": "provento",
            "kind": d.kind,
            "symbol": d.ticker,
            "day": d.paid_at,
            "settled_on": None,
            "quantity": d.quantity,
            "price": d.price,
            "amount": d.amount,
            "duplicate": _par_out_provento(lida.dividend_pairs[d.line])
            if d.line in lida.dividend_pairs
            else None,
        }
        for d in lida.parsed.dividends
    ]
    rows.sort(key=lambda r: r["line"])

    return {
        "format": FORMATO,
        "rows": rows,
        "issues": [i.as_dict() for i in lida.issues],
        "warnings": [w.as_dict() for w in lida.warnings],
        "ok": not lida.issues,
        "duplicates": sum(1 for r in rows if r["duplicate"] is not None),
    }


def commit(conteudo: bytes, include_lines: set[int]) -> dict:
    lida = _ler(conteudo, include_lines)

    if lida.issues:
        raise B3ImportRejected(
            f"{len(lida.issues)} linha(s) com problema. Corrija antes de importar: "
            + "; ".join(f"linha {i.line}: {i.message}" for i in lida.issues[:3])
        )

    operacoes = [
        op.entry
        for op in lida.parsed.operations
        if op.line not in lida.operation_pairs or op.line in include_lines
    ]
    proventos = [
        d
        for d in lida.parsed.dividends
        if d.line not in lida.dividend_pairs or d.line in include_lines
    ]
    total = len(lida.parsed.operations) + len(lida.parsed.dividends)

    ids = ledger_service.import_entries(operacoes)

    servico = DividendsService()
    dividend_ids = [
        servico.create(
            DividendReceivedCreate(
                ticker=d.ticker,
                paid_at=date.fromisoformat(d.paid_at),
                amount=d.amount,
                kind=d.kind,
                note="Importado do extrato da B3.",
            )
        ).id
        for d in proventos
    ]

    return {
        "operations": len(ids),
        "dividends": len(dividend_ids),
        "skipped_duplicates": total - len(ids) - len(dividend_ids),
        "ids": ids,
        "dividend_ids": dividend_ids,
    }
