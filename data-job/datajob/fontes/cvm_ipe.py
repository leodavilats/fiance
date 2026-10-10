from __future__ import annotations

import re

import sqlalchemy as sa

from datajob.banco import upsert
from datajob.erros import ArquivoInvalido
from datajob.esquema import ipe_documento
from datajob.fontes.cvm_comum import cnpj, data, ler_csv, membro_do_zip, nomes_do_zip

FONTE = "cvm_ipe"
PRIMEIRO_ANO = 2005

_BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS"
_ASSUNTO = re.compile(r"desdobr|grupam|bonifica|inplit|split", re.IGNORECASE)
_COLUNAS = {
    "CNPJ_Companhia",
    "Data_Referencia",
    "Categoria",
    "Tipo",
    "Especie",
    "Assunto",
    "Data_Entrega",
    "Protocolo_Entrega",
    "Versao",
    "Link_Download",
}


def url_do_ano(ano: int) -> str:
    return f"{_BASE}/ipe_cia_aberta_{ano}.zip"


def interpretar(conteudo: bytes) -> list[dict]:
    nomes = [n for n in nomes_do_zip(conteudo) if n.startswith("ipe_cia_aberta_")]
    if len(nomes) != 1:
        raise ArquivoInvalido("O ZIP do IPE não tem um arquivo de documentos.")

    documentos = {}
    for linha in ler_csv(membro_do_zip(conteudo, nomes[0]), _COLUNAS):
        texto = " ".join((linha["Assunto"], linha["Tipo"], linha["Especie"]))
        documento_cnpj, entrega = cnpj(linha["CNPJ_Companhia"]), data(linha["Data_Entrega"])
        if not _ASSUNTO.search(texto) or documento_cnpj is None or entrega is None:
            continue
        chave = (linha["Protocolo_Entrega"], linha["Versao"])
        documentos[chave] = {
            "protocolo": linha["Protocolo_Entrega"],
            "versao": int(linha["Versao"]) if linha["Versao"].isdigit() else 0,
            "cnpj": documento_cnpj,
            "data_entrega": entrega,
            "data_referencia": data(linha["Data_Referencia"]),
            "categoria": linha["Categoria"],
            "tipo": linha["Tipo"] or None,
            "especie": linha["Especie"] or None,
            "assunto": linha["Assunto"],
            "link": linha["Link_Download"] or None,
        }
    return list(documentos.values())


def processar(conn: sa.Connection, conteudo: bytes, coleta_id: int) -> tuple[int, int, int]:
    linhas = interpretar(conteudo)
    gravadas = upsert(
        conn,
        ipe_documento,
        [{**linha, "coleta_id": coleta_id} for linha in linhas],
        ["protocolo", "versao"],
    )
    return len(linhas), gravadas, 0
