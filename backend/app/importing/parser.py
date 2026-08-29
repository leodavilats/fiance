from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date

from app.ledger import LedgerEntry, LedgerError, TransactionKind

MAX_ROWS = 2000

_HEADER_ALIASES: dict[str, set[str]] = {
    "symbol": {"ticker", "ativo", "codigo", "código", "papel", "symbol", "ação", "acao"},
    "kind": {"tipo", "operacao", "operação", "movimento", "kind", "type", "c/v"},
    "traded_on": {
        "data",
        "date",
        "data da operacao",
        "data da operação",
        "dia",
        "pregao",
        "pregão",
    },
    "quantity": {"quantidade", "qtd", "qtde", "quantity", "qty"},
    "price": {
        "preco",
        "preço",
        "preco unitario",
        "preço unitário",
        "price",
        "valor unitario",
        "valor unitário",
        "cotacao",
        "cotação",
    },
    "fees": {"taxas", "custos", "corretagem", "fees", "emolumentos", "taxa"},
    "note": {"observacao", "observação", "nota", "note", "obs"},
}

_KIND_ALIASES: dict[str, TransactionKind] = {
    "c": TransactionKind.BUY,
    "compra": TransactionKind.BUY,
    "comprar": TransactionKind.BUY,
    "buy": TransactionKind.BUY,
    "entrada": TransactionKind.BUY,
    "v": TransactionKind.SELL,
    "venda": TransactionKind.SELL,
    "vender": TransactionKind.SELL,
    "sell": TransactionKind.SELL,
    "saida": TransactionKind.SELL,
    "saída": TransactionKind.SELL,
    "desdobramento": TransactionKind.SPLIT,
    "split": TransactionKind.SPLIT,
    "grupamento": TransactionKind.SPLIT,
    "bonificacao": TransactionKind.BONUS,
    "bonificação": TransactionKind.BONUS,
    "bonus": TransactionKind.BONUS,
    "amortizacao": TransactionKind.AMORTIZATION,
    "amortização": TransactionKind.AMORTIZATION,
    "transferencia de entrada": TransactionKind.TRANSFER_IN,
    "transferência de entrada": TransactionKind.TRANSFER_IN,
    "transferencia de saida": TransactionKind.TRANSFER_OUT,
    "transferência de saída": TransactionKind.TRANSFER_OUT,
}

_TICKER = re.compile(r"^[A-Z]{4}[0-9]{1,2}$")


@dataclass(frozen=True)
class ImportIssue:
    line: int
    message: str
    field: str | None = None
    raw: str = ""

    def as_dict(self) -> dict:
        return {"line": self.line, "message": self.message, "field": self.field, "raw": self.raw}


@dataclass
class ImportRow:
    line: int
    entry: LedgerEntry
    duplicate_of: int | None = None

    def as_dict(self) -> dict:
        return {
            "line": self.line,
            "kind": self.entry.kind.value,
            "symbol": self.entry.symbol,
            "traded_on": self.entry.traded_on,
            "quantity": self.entry.quantity,
            "price": self.entry.price,
            "fees": self.entry.fees,
            "ratio_from": self.entry.ratio_from,
            "ratio_to": self.entry.ratio_to,
            "amount": self.entry.amount,
            "note": self.entry.note,
            "duplicate_of": self.duplicate_of,
        }


@dataclass
class ParsedImport:
    rows: list[ImportRow] = field(default_factory=list)
    issues: list[ImportIssue] = field(default_factory=list)
    detected_format: str = "desconhecido"

    @property
    def ok(self) -> bool:
        return not self.issues

    def as_dict(self) -> dict:
        return {
            "format": self.detected_format,
            "rows": [row.as_dict() for row in self.rows],
            "issues": [issue.as_dict() for issue in self.issues],
            "ok": self.ok,
            "duplicates": sum(1 for row in self.rows if row.duplicate_of is not None),
        }


def _normalize_header(value: str) -> str | None:
    cleaned = value.strip().lower().strip('"').strip("'")
    for field_name, aliases in _HEADER_ALIASES.items():
        if cleaned in aliases:
            return field_name
    return None


def parse_decimal(raw: str, line: int, field_name: str) -> float:
    text = raw.strip().replace("R$", "").replace(" ", "").replace("\xa0", "")
    if not text:
        raise ValueError("valor vazio")

    negative = text.startswith("-")
    text = text.lstrip("+-")

    has_comma = "," in text
    has_dot = "." in text

    if has_comma and has_dot:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif has_comma:
        text = text.replace(",", ".")
    elif has_dot:
        inteiro, _, decimal = text.rpartition(".")
        if len(decimal) == 3 and inteiro:
            raise ValueError(
                f"{raw.strip()!r} é ambíguo: com três casas depois do ponto não dá para saber "
                "se é separador de milhar ou decimal. Escreva 1234.56 ou 1.234,56."
            )

    try:
        value = float(text)
    except ValueError as exc:
        raise ValueError(f"{raw.strip()!r} não é um número") from exc

    return -value if negative else value


def parse_day(raw: str, line: int) -> str:
    text = raw.strip()
    if not text:
        raise ValueError("data vazia")

    ano = mes = dia = None

    iso = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if iso:
        ano, mes, dia = (int(group) for group in iso.groups())
    else:
        br = re.fullmatch(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", text)
        if br:
            dia, mes, ano = (int(group) for group in br.groups())

    if ano is None:
        raise ValueError(f"{text!r} não é uma data reconhecida. Use DD/MM/AAAA ou AAAA-MM-DD.")

    try:
        return date(ano, mes, dia).strftime("%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"{text!r} não é um dia que existe no calendário.") from exc


def parse_kind(raw: str) -> TransactionKind:
    text = raw.strip().lower()
    kind = _KIND_ALIASES.get(text)
    if kind is None:
        conhecidos = "compra, venda, desdobramento, bonificação, amortização"
        raise ValueError(f"{raw.strip()!r} não é um tipo de operação. Use um de: {conhecidos}.")
    return kind


def parse_symbol(raw: str) -> str:
    text = raw.strip().upper().replace(".SA", "")
    if not text:
        raise ValueError("ativo vazio")
    if not _TICKER.fullmatch(text):
        raise ValueError(
            f"{raw.strip()!r} não parece um código da B3 (quatro letras e um ou dois dígitos)."
        )
    return text


def _detect_delimiter(sample: str) -> str:
    primeira = sample.splitlines()[0] if sample.splitlines() else ""
    if primeira.count(";") > primeira.count(","):
        return ";"
    if "\t" in primeira and primeira.count("\t") >= primeira.count(","):
        return "\t"
    return ","


def _row_to_entry(values: dict[str, str], line: int) -> LedgerEntry:
    kind = parse_kind(values.get("kind") or "compra")
    symbol = parse_symbol(values.get("symbol", ""))
    traded_on = parse_day(values.get("traded_on", ""), line)

    quantity = 0.0
    if values.get("quantity"):
        quantity = parse_decimal(values["quantity"], line, "quantidade")

    price = 0.0
    if values.get("price"):
        price = parse_decimal(values["price"], line, "preço")

    fees = 0.0
    if values.get("fees"):
        fees = parse_decimal(values["fees"], line, "taxas")

    amount = 0.0
    if kind is TransactionKind.AMORTIZATION:
        amount = price or quantity
        quantity = 0.0
        price = 0.0

    return LedgerEntry(
        kind=kind,
        symbol=symbol,
        traded_on=traded_on,
        quantity=quantity,
        price=price,
        fees=fees,
        amount=amount,
        note=(values.get("note") or "").strip() or None,
    )


def _parse_csv(text: str, result: ParsedImport) -> None:
    delimiter = _detect_delimiter(text)
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)

    rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not rows:
        result.issues.append(ImportIssue(line=0, message="Arquivo vazio."))
        return

    header = [_normalize_header(cell) for cell in rows[0]]
    if "symbol" not in header:
        result.issues.append(
            ImportIssue(
                line=1,
                message=(
                    "Não encontrei a coluna do ativo. O cabeçalho precisa ter uma coluna "
                    "chamada Ticker, Ativo, Código ou Papel."
                ),
                raw=delimiter.join(rows[0]),
            )
        )
        return

    result.detected_format = f"csv (separador {delimiter!r})"

    for index, row in enumerate(rows[1:], start=2):
        values = {
            name: row[position].strip()
            for position, name in enumerate(header)
            if name and position < len(row)
        }
        _consume(values, index, delimiter.join(row), result)


_LIST_TOKENS = re.compile(r"[\s;]+")
_LIST_TOKENS_FALLBACK = re.compile(r"[\s,;]+")


def _parse_list(text: str, result: ParsedImport, default_day: str) -> None:
    result.detected_format = "lista colada"

    for index, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        tokens = [t for t in _LIST_TOKENS.split(line) if t]
        if len(tokens) < 3 and "," in line:
            tokens = [t for t in _LIST_TOKENS_FALLBACK.split(line) if t]

        if len(tokens) < 3:
            result.issues.append(
                ImportIssue(
                    line=index,
                    message=(
                        "Esperava ao menos ativo, quantidade e preço. Exemplo: PETR4 100 30,50"
                    ),
                    raw=line,
                )
            )
            continue

        kind_token = tokens[0].lower() if tokens[0].lower() in _KIND_ALIASES else None
        if kind_token:
            tokens = tokens[1:]

        if len(tokens) < 3:
            result.issues.append(
                ImportIssue(line=index, message="Faltou quantidade ou preço.", raw=line)
            )
            continue

        values = {
            "kind": kind_token or "compra",
            "symbol": tokens[0],
            "quantity": tokens[1],
            "price": tokens[2],
            "traded_on": tokens[3] if len(tokens) > 3 else default_day,
            "fees": tokens[4] if len(tokens) > 4 else "",
        }
        _consume(values, index, line, result)


def _consume(values: dict[str, str], line: int, raw: str, result: ParsedImport) -> None:
    try:
        entry = _row_to_entry(values, line)
    except (ValueError, LedgerError) as exc:
        result.issues.append(ImportIssue(line=line, message=str(exc), raw=raw))
        return

    result.rows.append(ImportRow(line=line, entry=entry))


def parse_import(text: str, default_day: str, force_format: str | None = None) -> ParsedImport:
    result = ParsedImport()

    content = text.strip()
    if not content:
        result.issues.append(ImportIssue(line=0, message="Nada para importar."))
        return result

    linhas = content.splitlines()
    if len(linhas) > MAX_ROWS:
        result.issues.append(
            ImportIssue(
                line=0,
                message=(
                    f"São {len(linhas)} linhas e o limite é {MAX_ROWS}. Divida o arquivo por ano."
                ),
            )
        )
        return result

    formato = force_format
    if formato is None:
        primeira = linhas[0]
        tem_cabecalho = any(_normalize_header(cell) for cell in re.split(r"[;,\t]", primeira))
        formato = "csv" if tem_cabecalho else "list"

    if formato == "csv":
        _parse_csv(content, result)
    else:
        _parse_list(content, result, default_day)

    return result
