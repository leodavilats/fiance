from __future__ import annotations

import sqlalchemy as sa

from datajob.banco import upsert
from datajob.erros import ArquivoInvalido
from datajob.esquema import capital_social
from datajob.fontes.cvm_comum import cnpj, data, ler_csv, membro_do_zip, nomes_do_zip

FONTE = "cvm_fre"
PRIMEIRO_ANO = 2010

_BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS"
_PREFIXO = "fre_cia_aberta_capital_social_"
_INTEGRALIZADO = "Capital Integralizado"
_COLUNAS = {
    "CNPJ_Companhia",
    "Data_Referencia",
    "Versao",
    "Tipo_Capital",
    "Data_Autorizacao_Aprovacao",
    "Quantidade_Acoes_Ordinarias",
    "Quantidade_Acoes_Preferenciais",
    "Quantidade_Total_Acoes",
}
_CHAVE = ["cnpj", "data_referencia", "versao", "data_aprovacao"]


def url_do_ano(ano: int) -> str:
    return f"{_BASE}/fre_cia_aberta_{ano}.zip"


def _inteiro(texto: str) -> int | None:
    try:
        return int(float(texto)) if texto else None
    except ValueError:
        return None


def interpretar(conteudo: bytes) -> list[dict]:
    nomes = [
        n for n in nomes_do_zip(conteudo) if n.startswith(_PREFIXO) and n[len(_PREFIXO)].isdigit()
    ]
    if len(nomes) != 1:
        raise ArquivoInvalido("O ZIP do FRE não tem o arquivo de capital social.")

    linhas = {}
    for linha in ler_csv(membro_do_zip(conteudo, nomes[0]), _COLUNAS):
        if linha["Tipo_Capital"] != _INTEGRALIZADO:
            continue
        registro = {
            "cnpj": cnpj(linha["CNPJ_Companhia"]),
            "data_referencia": data(linha["Data_Referencia"]),
            "versao": _inteiro(linha["Versao"]),
            "data_aprovacao": data(linha["Data_Autorizacao_Aprovacao"]),
            "acoes_ordinarias": _inteiro(linha["Quantidade_Acoes_Ordinarias"]),
            "acoes_preferenciais": _inteiro(linha["Quantidade_Acoes_Preferenciais"]),
            "acoes_total": _inteiro(linha["Quantidade_Total_Acoes"]),
        }
        if None in (registro[c] for c in _CHAVE) or not registro["acoes_total"]:
            continue
        linhas[tuple(registro[c] for c in _CHAVE)] = registro
    return list(linhas.values())


def processar(conn: sa.Connection, conteudo: bytes, coleta_id: int) -> tuple[int, int, int]:
    linhas = interpretar(conteudo)
    gravadas = upsert(
        conn, capital_social, [{**linha, "coleta_id": coleta_id} for linha in linhas], _CHAVE
    )
    return len(linhas), gravadas, 0
