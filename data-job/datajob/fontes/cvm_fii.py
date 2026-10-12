from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal, InvalidOperation

import sqlalchemy as sa

from datajob.erros import ArquivoInvalido
from datajob.fontes.cvm_comum import cnpj, data, ler_csv, membro_do_zip, nomes_do_zip

FONTE = "cvm_fii"
PRIMEIRO_ANO = 2016
ORIGEM = "cvm_estimado"

_BASE = "https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/DADOS"
_GERAL = {"CNPJ_Fundo_Classe", "Data_Referencia", "Versao", "Codigo_ISIN"}
_COMPLEMENTO = {
    "CNPJ_Fundo_Classe",
    "Data_Referencia",
    "Versao",
    "Valor_Patrimonial_Cotas",
    "Percentual_Dividend_Yield_Mes",
}
_YIELD_PLAUSIVEL = Decimal("0.1")


def url_do_ano(ano: int) -> str:
    return f"{_BASE}/inf_mensal_fii_{ano}.zip"


def _membro(conteudo: bytes, prefixo: str) -> bytes:
    nomes = [n for n in nomes_do_zip(conteudo) if n.startswith(prefixo)]
    if len(nomes) != 1:
        raise ArquivoInvalido(f"O ZIP do informe mensal de FII não tem {prefixo}*.")
    cabecalho, _, resto = membro_do_zip(conteudo, nomes[0]).partition(b"\n")
    colunas = [b"CNPJ_Fundo_Classe" if c == b"CNPJ_Fundo" else c for c in cabecalho.split(b";")]
    return b";".join(colunas) + b"\n" + resto


def _decimal(texto: str) -> Decimal | None:
    try:
        return Decimal(texto) if texto else None
    except InvalidOperation:
        return None


def _ultima_versao(linhas: list[dict]) -> dict[tuple[str, date], dict]:
    escolhidas: dict[tuple[str, date], dict] = {}
    for linha in linhas:
        chave = (cnpj(linha["CNPJ_Fundo_Classe"]), data(linha["Data_Referencia"]))
        if None in chave:
            continue
        atual = escolhidas.get(chave)
        if atual is None or int(linha["Versao"] or 0) >= int(atual["Versao"] or 0):
            escolhidas[chave] = linha
    return escolhidas


def interpretar(conteudo: bytes) -> tuple[list[dict], list[tuple[str, str]]]:
    geral = _ultima_versao(ler_csv(_membro(conteudo, "inf_mensal_fii_geral_"), _GERAL))
    complemento = _ultima_versao(
        ler_csv(_membro(conteudo, "inf_mensal_fii_complemento_"), _COMPLEMENTO)
    )

    proventos, rejeitados = {}, []
    for (documento, referencia), linha in complemento.items():
        isin = (geral.get((documento, referencia)) or {}).get("Codigo_ISIN", "").upper()
        dy = _decimal(linha["Percentual_Dividend_Yield_Mes"])
        cota = _decimal(linha["Valor_Patrimonial_Cotas"])
        if len(isin) != 12 or not isin.startswith("BR") or not dy or not cota or cota <= 0:
            continue
        if not 0 < dy <= _YIELD_PLAUSIVEL:
            rejeitados.append((f"{isin} {referencia}", f"yield do mês implausível: {dy}"))
            continue
        ultimo_dia = calendar.monthrange(referencia.year, referencia.month)[1]
        data_com = referencia.replace(day=ultimo_dia)
        proventos[(isin[2:6], data_com)] = {
            "emissor": isin[2:6],
            "classe": "CI",
            "data_com": data_com,
            "tipo": "RENDIMENTO",
            "valor": round(dy * cota, 6),
        }
    return list(proventos.values()), rejeitados


def processar(conn: sa.Connection, conteudo: bytes, coleta_id: int) -> tuple[int, int, int]:
    proventos, rejeitados = interpretar(conteudo)
    for ano in {p["data_com"].year for p in proventos}:
        conn.execute(
            sa.text(
                "DELETE FROM mercado.provento WHERE origem = :o "
                "AND data_com >= make_date(:a, 1, 1) AND data_com < make_date(:a + 1, 1, 1)"
            ),
            {"o": ORIGEM, "a": ano},
        )
    if proventos:
        conn.execute(
            sa.text(
                "INSERT INTO mercado.provento (emissor, classe, data_com, tipo, valor, origem, "
                "coleta_id) VALUES (:emissor, :classe, :data_com, :tipo, :valor, :origem, "
                ":coleta_id)"
            ),
            [{**p, "origem": ORIGEM, "coleta_id": coleta_id} for p in proventos],
        )
    if rejeitados:
        conn.execute(
            sa.text(
                "INSERT INTO mercado.quarentena (coleta_id, chave, motivo, conteudo) "
                "VALUES (:coleta_id, :chave, :motivo, :chave)"
            ),
            [{"coleta_id": coleta_id, "chave": c, "motivo": m} for c, m in rejeitados],
        )
    return len(proventos) + len(rejeitados), len(proventos), len(rejeitados)
