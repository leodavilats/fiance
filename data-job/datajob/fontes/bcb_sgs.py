from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

import sqlalchemy as sa

from datajob.banco import upsert
from datajob.erros import ArquivoInvalido
from datajob.esquema import indicador

FONTE = "bcb_sgs"
PRIMEIRA_DATA = date(2005, 1, 1)

SERIES = {
    12: "CDI diário (% ao dia)",
    11: "Selic diária (% ao dia)",
    432: "Meta da Selic (% ao ano)",
    433: "IPCA mensal (%)",
}

_JANELA = timedelta(days=365 * 10 - 5)
_RECOBRIR = timedelta(days=45)
_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados?formato=json&dataInicial={inicio:%d/%m/%Y}&dataFinal={fim:%d/%m/%Y}"


def url(serie: int, inicio: date, fim: date) -> str:
    return _URL.format(serie=serie, inicio=inicio, fim=fim)


def nome(serie: int, inicio: date, fim: date) -> str:
    return f"sgs_{serie}_{inicio:%Y%m%d}_{fim:%Y%m%d}.json"


def janelas(ultima: date | None, hoje: date) -> list[tuple[date, date]]:
    inicio = PRIMEIRA_DATA if ultima is None else max(PRIMEIRA_DATA, ultima - _RECOBRIR)
    saida = []
    while inicio <= hoje:
        fim = min(inicio + _JANELA, hoje)
        saida.append((inicio, fim))
        inicio = fim + timedelta(days=1)
    return saida


def interpretar(conteudo: bytes, serie: int) -> tuple[list[dict], list[tuple[str, str]]]:
    try:
        pontos = json.loads(conteudo)
    except ValueError as e:
        raise ArquivoInvalido(f"A série {serie} do BCB não veio em JSON.") from e
    if not isinstance(pontos, list):
        raise ArquivoInvalido(f"A série {serie} do BCB veio com erro: {str(pontos)[:200]}")

    linhas, rejeitadas = {}, []
    for ponto in pontos:
        try:
            dia = datetime.strptime(ponto["data"], "%d/%m/%Y").date()
            valor = Decimal(ponto["valor"])
        except (KeyError, TypeError, ValueError, InvalidOperation):
            rejeitadas.append((f"{serie} {ponto}", "ponto ilegível"))
            continue
        linhas[dia] = {"serie": serie, "data": dia, "valor": valor}
    return list(linhas.values()), rejeitadas


def processador(serie: int) -> Callable[[sa.Connection, bytes, int], tuple[int, int, int]]:
    def processar(conn: sa.Connection, conteudo: bytes, coleta_id: int) -> tuple[int, int, int]:
        linhas, rejeitadas = interpretar(conteudo, serie)
        gravadas = upsert(
            conn,
            indicador,
            [{**linha, "coleta_id": coleta_id} for linha in linhas],
            ["serie", "data"],
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

    return processar
