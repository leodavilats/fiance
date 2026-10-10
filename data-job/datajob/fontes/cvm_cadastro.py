from __future__ import annotations

import sqlalchemy as sa

from datajob.banco import upsert
from datajob.esquema import empresa
from datajob.fontes.cvm_comum import cnpj, data, ler_csv

FONTE = "cvm_cadastro"
URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
NOME = "cad_cia_aberta.csv"

_COLUNAS = {
    "CNPJ_CIA",
    "DENOM_SOCIAL",
    "DENOM_COMERC",
    "DT_REG",
    "DT_CANCEL",
    "MOTIVO_CANCEL",
    "SIT",
    "CD_CVM",
    "SETOR_ATIV",
    "SIT_EMISSOR",
    "CONTROLE_ACIONARIO",
}


def _preferida(atual: dict, nova: dict) -> dict:
    def chave(linha: dict) -> tuple:
        return (linha["DT_CANCEL"] == "", linha["DT_CANCEL"], linha["DT_REG"])

    return nova if chave(nova) > chave(atual) else atual


def interpretar(conteudo: bytes) -> list[dict]:
    por_cnpj: dict[str, dict] = {}
    for linha in ler_csv(conteudo, _COLUNAS):
        documento = cnpj(linha["CNPJ_CIA"])
        if documento is None:
            continue
        atual = por_cnpj.get(documento)
        por_cnpj[documento] = linha if atual is None else _preferida(atual, linha)

    return [
        {
            "cnpj": documento,
            "codigo_cvm": linha["CD_CVM"] or None,
            "razao_social": linha["DENOM_SOCIAL"],
            "nome_comercial": linha["DENOM_COMERC"] or None,
            "setor": linha["SETOR_ATIV"] or None,
            "situacao": linha["SIT"] or None,
            "situacao_emissor": linha["SIT_EMISSOR"] or None,
            "controle_acionario": linha["CONTROLE_ACIONARIO"] or None,
            "data_registro": data(linha["DT_REG"]),
            "data_cancelamento": data(linha["DT_CANCEL"]),
            "motivo_cancelamento": linha["MOTIVO_CANCEL"] or None,
        }
        for documento, linha in por_cnpj.items()
    ]


def processar(conn: sa.Connection, conteudo: bytes, coleta_id: int) -> tuple[int, int, int]:
    linhas = interpretar(conteudo)
    gravadas = upsert(
        conn, empresa, [{**linha, "coleta_id": coleta_id} for linha in linhas], ["cnpj"]
    )
    return len(linhas), gravadas, 0
