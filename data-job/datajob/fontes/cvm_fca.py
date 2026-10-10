from __future__ import annotations

import sqlalchemy as sa

from datajob.banco import upsert
from datajob.esquema import valor_mobiliario
from datajob.fontes.cvm_comum import (
    ArquivoInvalido,
    cnpj,
    data,
    ler_csv,
    membro_do_zip,
    nomes_do_zip,
)

FONTE = "cvm_fca"
PRIMEIRO_ANO = 2010

_BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS"

_COLUNAS = {
    "CNPJ_Companhia",
    "Data_Referencia",
    "Versao",
    "ID_Documento",
    "Valor_Mobiliario",
    "Sigla_Classe_Acao_Preferencial",
    "Codigo_Negociacao",
    "Mercado",
    "Segmento",
    "Data_Inicio_Negociacao",
    "Data_Fim_Negociacao",
    "Data_Inicio_Listagem",
    "Data_Fim_Listagem",
}


def url_do_ano(ano: int) -> str:
    return f"{_BASE}/fca_cia_aberta_{ano}.zip"


_PREFIXO = "fca_cia_aberta_valor_mobiliario_"

_CHAVE = ["cnpj", "data_referencia", "versao", "tipo", "classe", "codigo"]


def interpretar(conteudo: bytes) -> list[dict]:
    nomes = [n for n in nomes_do_zip(conteudo) if n.startswith(_PREFIXO)]
    if len(nomes) != 1:
        raise ArquivoInvalido("O ZIP do FCA não tem um arquivo de valores mobiliários.")
    linhas = ler_csv(membro_do_zip(conteudo, nomes[0]), _COLUNAS)

    por_chave: dict[tuple, dict] = {}
    for linha in linhas:
        documento = cnpj(linha["CNPJ_Companhia"])
        referencia = data(linha["Data_Referencia"])
        if documento is None or referencia is None or not linha["Versao"].isdigit():
            continue
        registro = {
            "cnpj": documento,
            "data_referencia": referencia,
            "versao": int(linha["Versao"]),
            "tipo": linha["Valor_Mobiliario"],
            "classe": linha["Sigla_Classe_Acao_Preferencial"],
            "codigo": linha["Codigo_Negociacao"].upper(),
            "id_documento": linha["ID_Documento"],
            "mercado": linha["Mercado"] or None,
            "segmento": linha["Segmento"] or None,
            "inicio_negociacao": data(linha["Data_Inicio_Negociacao"]),
            "fim_negociacao": data(linha["Data_Fim_Negociacao"]),
            "inicio_listagem": data(linha["Data_Inicio_Listagem"]),
            "fim_listagem": data(linha["Data_Fim_Listagem"]),
        }
        chave = tuple(registro[c] for c in _CHAVE)
        por_chave.setdefault(chave, registro)
    return list(por_chave.values())


def processar(conn: sa.Connection, conteudo: bytes, coleta_id: int) -> tuple[int, int, int]:
    linhas = interpretar(conteudo)
    gravadas = upsert(
        conn, valor_mobiliario, [{**linha, "coleta_id": coleta_id} for linha in linhas], _CHAVE
    )
    return len(linhas), gravadas, 0
