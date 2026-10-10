from __future__ import annotations

import base64
import json
from collections.abc import Callable
from datetime import datetime

import sqlalchemy as sa

from datajob.banco import upsert
from datajob.esquema import emissor_b3
from datajob.fontes.cvm_comum import ArquivoInvalido, cnpj

FONTE = "b3_emissores"
NOME = "b3_emissores.json"

_URL = (
    "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetInitialCompanies/"
)
_POR_PAGINA = 120


def url_da_pagina(pagina: int) -> str:
    consulta = {"language": "pt-br", "pageNumber": pagina, "pageSize": _POR_PAGINA}
    return _URL + base64.b64encode(json.dumps(consulta).encode()).decode()


def baixar_lista(baixar: Callable[[str], bytes]) -> bytes:
    emissores, pagina, paginas = [], 1, 1
    while pagina <= paginas:
        resposta = json.loads(baixar(url_da_pagina(pagina)))
        paginas = resposta["page"]["totalPages"]
        emissores += resposta["results"]
        pagina += 1
    emissores.sort(key=lambda e: e["issuingCompany"])
    return json.dumps(emissores, ensure_ascii=False, sort_keys=True).encode()


def _data(texto: str):
    try:
        lida = datetime.strptime(texto, "%d/%m/%Y").date()
    except (TypeError, ValueError):
        return None
    return None if lida.year == 9999 else lida


def interpretar(conteudo: bytes) -> list[dict]:
    try:
        emissores = json.loads(conteudo)
    except ValueError as e:
        raise ArquivoInvalido("A lista de emissores da B3 não é JSON.") from e
    linhas = {}
    for e in emissores:
        codigo = (e.get("issuingCompany") or "").strip().upper()
        if len(codigo) != 4:
            continue
        linhas[codigo] = {
            "codigo": codigo,
            "cnpj": cnpj(e.get("cnpj") or ""),
            "codigo_cvm": e.get("codeCVM") or None,
            "razao_social": e.get("companyName") or "",
            "nome_pregao": e.get("tradingName") or None,
            "segmento": e.get("segment") or None,
            "tipo": e.get("type") or None,
            "data_listagem": _data(e.get("dateListing")),
        }
    return list(linhas.values())


def processar(conn: sa.Connection, conteudo: bytes, coleta_id: int) -> tuple[int, int, int]:
    linhas = interpretar(conteudo)
    gravadas = upsert(
        conn, emissor_b3, [{**linha, "coleta_id": coleta_id} for linha in linhas], ["codigo"]
    )
    return len(linhas), gravadas, 0
