from __future__ import annotations

import csv
import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import sqlalchemy as sa

from datajob.banco import upsert
from datajob.erros import ArquivoInvalido
from datajob.esquema import tesouro

FONTE = "tesouro_direto"
URL = (
    "https://www.tesourotransparente.gov.br/ckan/dataset/df56aa42-484a-4a59-8184-7676580c81e3"
    "/resource/796d2059-14e9-44e3-80c9-2d9e30b405c1/download/PrecoTaxaTesouroDireto.csv"
)
NOME = "PrecoTaxaTesouroDireto.csv"

_COLUNAS = {
    "Tipo Titulo",
    "Data Vencimento",
    "Data Base",
    "Taxa Compra Manha",
    "Taxa Venda Manha",
    "PU Compra Manha",
    "PU Venda Manha",
    "PU Base Manha",
}


def _data(texto: str) -> date | None:
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def _numero(texto: str) -> Decimal | None:
    try:
        return Decimal(texto.strip().replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def _lado(taxa: Decimal | None, pu: Decimal | None) -> tuple[Decimal | None, Decimal | None]:
    if not pu:
        return None, None
    return taxa, pu


def interpretar(conteudo: bytes) -> tuple[list[dict], list[tuple[str, str]]]:
    leitor = csv.DictReader(io.StringIO(conteudo.decode("latin-1")), delimiter=";")
    faltando = _COLUNAS - set(leitor.fieldnames or ())
    if faltando:
        raise ArquivoInvalido(f"Faltam colunas no CSV do Tesouro Direto: {sorted(faltando)}.")

    linhas, rejeitadas = {}, []
    for bruta in leitor:
        titulo = (bruta["Tipo Titulo"] or "").strip()
        vencimento, dia = _data(bruta["Data Vencimento"] or ""), _data(bruta["Data Base"] or "")
        if not titulo or vencimento is None or dia is None:
            rejeitadas.append((str(bruta)[:200], "linha ilegível"))
            continue
        taxa_compra, pu_compra = _lado(
            _numero(bruta["Taxa Compra Manha"]), _numero(bruta["PU Compra Manha"])
        )
        taxa_venda, pu_venda = _lado(
            _numero(bruta["Taxa Venda Manha"]), _numero(bruta["PU Venda Manha"])
        )
        linhas[(titulo, vencimento, dia)] = {
            "titulo": titulo,
            "vencimento": vencimento,
            "data": dia,
            "taxa_compra": taxa_compra,
            "taxa_venda": taxa_venda,
            "pu_compra": pu_compra,
            "pu_venda": pu_venda,
            "pu_base": _numero(bruta["PU Base Manha"]) or None,
        }
    return list(linhas.values()), rejeitadas


def processar(conn: sa.Connection, conteudo: bytes, coleta_id: int) -> tuple[int, int, int]:
    linhas, rejeitadas = interpretar(conteudo)
    gravadas = upsert(
        conn,
        tesouro,
        [{**linha, "coleta_id": coleta_id} for linha in linhas],
        ["titulo", "vencimento", "data"],
    )
    if rejeitadas:
        conn.execute(
            sa.text(
                "INSERT INTO mercado.quarentena (coleta_id, chave, motivo, conteudo) "
                "VALUES (:coleta_id, :chave, :motivo, :chave)"
            ),
            [{"coleta_id": coleta_id, "chave": c, "motivo": m} for c, m in rejeitadas],
        )
    return len(linhas) + len(rejeitadas), gravadas, len(rejeitadas)
