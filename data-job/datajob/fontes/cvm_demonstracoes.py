from __future__ import annotations

import csv
import io
import re
import zipfile
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation

import sqlalchemy as sa

from datajob.banco import upsert
from datajob.erros import ArquivoInvalido
from datajob.esquema import documento
from datajob.fontes.cvm_comum import cnpj, data

DEMONSTRACOES = ("BPA", "BPP", "DRE", "DFC_MI", "DFC_MD")
PRIMEIRO_ANO = {"DFP": 2010, "ITR": 2011}
FONTE = {"DFP": "cvm_dfp", "ITR": "cvm_itr"}

_BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC"
_ESCALA = {"MIL": Decimal(1000), "UNIDADE": Decimal(1)}
_EXERCICIO_CORRENTE = "ÚLTIMO"


def url_do_ano(tipo: str, ano: int) -> str:
    return f"{_BASE}/{tipo}/DADOS/{tipo.lower()}_cia_aberta_{ano}.zip"


@dataclass(frozen=True)
class Linha:
    cnpj: str
    data_referencia: date
    versao: int
    demonstracao: str
    inicio_exercicio: date
    fim_exercicio: date
    conta: str
    consolidado: bool
    descricao: str
    valor: Decimal
    conta_fixa: bool

    def chave(self) -> tuple:
        return (
            self.cnpj,
            self.data_referencia,
            self.versao,
            self.demonstracao,
            self.inicio_exercicio,
            self.fim_exercicio,
            self.conta,
        )


@dataclass(frozen=True)
class Rejeitada:
    chave: str
    motivo: str
    conteudo: str


@dataclass
class Leitura:
    documentos: list[dict] = field(default_factory=list)
    linhas: list[Linha] = field(default_factory=list)
    rejeitadas: list[Rejeitada] = field(default_factory=list)
    lidas: int = 0


def _csv(arquivo: zipfile.ZipFile, nome: str) -> Iterator[dict[str, str]]:
    with io.TextIOWrapper(arquivo.open(nome), encoding="latin-1", newline="") as texto:
        yield from csv.DictReader(texto, delimiter=";")


def _documentos(arquivo: zipfile.ZipFile, nome: str, tipo: str) -> list[dict]:
    documentos = {}
    for r in _csv(arquivo, nome):
        documento_cnpj, referencia = cnpj(r["CNPJ_CIA"]), data(r["DT_REFER"])
        if documento_cnpj is None or referencia is None or not r["VERSAO"].isdigit():
            continue
        chave = (documento_cnpj, referencia, int(r["VERSAO"]))
        documentos[chave] = {
            "cnpj": documento_cnpj,
            "tipo": tipo,
            "data_referencia": referencia,
            "versao": int(r["VERSAO"]),
            "codigo_cvm": (r.get("CD_CVM") or "").strip() or None,
            "id_documento": (r.get("ID_DOC") or "").strip() or None,
            "data_entrega": data(r.get("DT_RECEB") or ""),
        }
    return list(documentos.values())


def _linha(r: dict[str, str], demonstracao: str, consolidado: bool) -> Linha | str:
    documento_cnpj, referencia, fim = (
        cnpj(r["CNPJ_CIA"]),
        data(r["DT_REFER"]),
        data(r["DT_FIM_EXERC"]),
    )
    if documento_cnpj is None or referencia is None or fim is None or not r["VERSAO"].isdigit():
        return "campo ilegível"
    if r["MOEDA"] != "REAL":
        return f"moeda {r['MOEDA']!r}"
    escala = _ESCALA.get(r["ESCALA_MOEDA"])
    if escala is None:
        return f"escala {r['ESCALA_MOEDA']!r}"
    try:
        valor = Decimal(r["VL_CONTA"]) * escala
    except InvalidOperation:
        return "valor ilegível"
    return Linha(
        cnpj=documento_cnpj,
        data_referencia=referencia,
        versao=int(r["VERSAO"]),
        demonstracao=demonstracao,
        inicio_exercicio=data(r.get("DT_INI_EXERC") or "") or fim,
        fim_exercicio=fim,
        conta=r["CD_CONTA"].strip(),
        consolidado=consolidado,
        descricao=r["DS_CONTA"].strip(),
        valor=valor,
        conta_fixa=r["ST_CONTA_FIXA"] == "S",
    )


def interpretar(conteudo: bytes, tipo: str, com_acao: set[str] | None = None) -> Leitura:
    prefixo = tipo.lower()
    try:
        arquivo = zipfile.ZipFile(io.BytesIO(conteudo))
    except zipfile.BadZipFile as e:
        raise ArquivoInvalido("O conteúdo baixado não é um ZIP.") from e

    with arquivo:
        nomes = arquivo.namelist()
        indice = [n for n in nomes if re.fullmatch(rf"{prefixo}_cia_aberta_\d{{4}}\.csv", n)]
        if len(indice) != 1:
            raise ArquivoInvalido(f"O ZIP da {tipo} não tem o índice de documentos.")
        leitura = Leitura(documentos=_documentos(arquivo, indice[0], tipo))

        padrao = re.compile(
            rf"{prefixo}_cia_aberta_({'|'.join(DEMONSTRACOES)})_(con|ind)_\d{{4}}\.csv"
        )
        demonstracoes = sorted(
            (m.group(2) == "con", m.group(1), n) for n in nomes if (m := padrao.fullmatch(n))
        )
        com_consolidado: set[tuple] = set()
        por_chave: dict[tuple, Linha] = {}
        conflitos: set[tuple] = set()
        for consolidado, demonstracao, nome in reversed(demonstracoes):
            for r in _csv(arquivo, nome):
                if r["ORDEM_EXERC"] != _EXERCICIO_CORRENTE:
                    continue
                documento_cnpj = cnpj(r["CNPJ_CIA"])
                if com_acao is not None and documento_cnpj not in com_acao:
                    continue
                chave_documento = (documento_cnpj, r["DT_REFER"], r["VERSAO"])
                if consolidado:
                    com_consolidado.add(chave_documento)
                elif chave_documento in com_consolidado:
                    continue
                leitura.lidas += 1
                linha = _linha(r, demonstracao, consolidado)
                if isinstance(linha, str):
                    chave = f"{r['CNPJ_CIA']} {r['DT_REFER']} {demonstracao} {r['CD_CONTA']}"
                    leitura.rejeitadas.append(Rejeitada(chave, linha, ";".join(r.values())))
                    continue
                anterior = por_chave.get(linha.chave())
                if anterior is None:
                    por_chave[linha.chave()] = linha
                elif (anterior.valor, anterior.descricao) != (linha.valor, linha.descricao):
                    conflitos.add(linha.chave())

    for chave in conflitos:
        linha = por_chave.pop(chave)
        leitura.rejeitadas.append(
            Rejeitada(
                " ".join(str(c) for c in chave),
                "conta repetida com valores diferentes",
                f"{linha.descricao};{linha.valor}",
            )
        )
    leitura.linhas = list(por_chave.values())
    return leitura


_COLUNAS = (
    "cnpj",
    "data_referencia",
    "versao",
    "demonstracao",
    "inicio_exercicio",
    "fim_exercicio",
    "conta",
    "consolidado",
    "descricao",
    "valor",
    "conta_fixa",
)

_CRIAR_CARGA = """
CREATE TEMP TABLE _linha (
    cnpj text, data_referencia date, versao integer, demonstracao text,
    inicio_exercicio date, fim_exercicio date, conta text, consolidado boolean,
    descricao text, valor numeric, conta_fixa boolean
) ON COMMIT DROP
"""

_SEM_DOCUMENTO = """
INSERT INTO mercado.quarentena (coleta_id, chave, motivo, conteudo)
SELECT :coleta_id, l.cnpj || ' ' || l.data_referencia || ' v' || l.versao,
       'linha sem documento no índice', l.demonstracao || ' ' || l.conta
FROM _linha l
LEFT JOIN mercado.documento d
  ON d.cnpj = l.cnpj AND d.tipo = :tipo AND d.data_referencia = l.data_referencia
 AND d.versao = l.versao
WHERE d.id IS NULL
"""

_CAMPOS = ("consolidado", "descricao", "valor", "conta_fixa")

_GRAVAR = f"""
INSERT INTO mercado.demonstracao_linha AS x
    (documento_id, demonstracao, inicio_exercicio, fim_exercicio, conta, {", ".join(_CAMPOS)},
     coleta_id)
SELECT d.id, l.demonstracao, l.inicio_exercicio, l.fim_exercicio, l.conta,
       {", ".join(f"l.{c}" for c in _CAMPOS)}, :coleta_id
FROM _linha l
JOIN mercado.documento d
  ON d.cnpj = l.cnpj AND d.tipo = :tipo AND d.data_referencia = l.data_referencia
 AND d.versao = l.versao
ON CONFLICT (documento_id, demonstracao, inicio_exercicio, fim_exercicio, conta) DO UPDATE SET
    {", ".join(f"{c} = EXCLUDED.{c}" for c in _CAMPOS)}, coleta_id = EXCLUDED.coleta_id
WHERE ({", ".join(f"x.{c}" for c in _CAMPOS)})
      IS DISTINCT FROM ({", ".join(f"EXCLUDED.{c}" for c in _CAMPOS)})
"""


def gravar(conn: sa.Connection, leitura: Leitura, tipo: str, coleta_id: int) -> tuple[int, int]:
    gravadas = upsert(
        conn,
        documento,
        [{**d, "coleta_id": coleta_id} for d in leitura.documentos],
        ["cnpj", "tipo", "data_referencia", "versao"],
    )

    conn.execute(sa.text(_CRIAR_CARGA))
    cursor = conn.connection.driver_connection.cursor()
    with cursor.copy(f"COPY _linha ({', '.join(_COLUNAS)}) FROM STDIN") as copia:
        for linha in leitura.linhas:
            copia.write_row(tuple(getattr(linha, c) for c in _COLUNAS))

    parametros = {"coleta_id": coleta_id, "tipo": tipo}
    sem_documento = conn.execute(sa.text(_SEM_DOCUMENTO), parametros).rowcount
    gravadas += conn.execute(sa.text(_GRAVAR), parametros).rowcount

    if leitura.rejeitadas:
        conn.execute(
            sa.text(
                "INSERT INTO mercado.quarentena (coleta_id, chave, motivo, conteudo) "
                "VALUES (:coleta_id, :chave, :motivo, :conteudo)"
            ),
            [
                {
                    "coleta_id": coleta_id,
                    "chave": r.chave,
                    "motivo": r.motivo,
                    "conteudo": r.conteudo,
                }
                for r in leitura.rejeitadas
            ],
        )
    return gravadas, sem_documento


def _inteiro(texto: str) -> int | None:
    try:
        return int(Decimal(texto)) if texto else None
    except InvalidOperation:
        return None


def interpretar_composicao(conteudo: bytes, tipo: str) -> list[dict]:
    prefixo = tipo.lower()
    try:
        arquivo = zipfile.ZipFile(io.BytesIO(conteudo))
    except zipfile.BadZipFile as e:
        raise ArquivoInvalido("O conteúdo baixado não é um ZIP.") from e
    with arquivo:
        nomes = [
            n
            for n in arquivo.namelist()
            if re.fullmatch(rf"{prefixo}_cia_aberta_composicao_capital_\d{{4}}\.csv", n)
        ]
        linhas = {}
        for nome in nomes:
            for r in _csv(arquivo, nome):
                documento_cnpj, referencia = cnpj(r["CNPJ_CIA"]), data(r["DT_REFER"])
                if documento_cnpj is None or referencia is None or not r["VERSAO"].isdigit():
                    continue
                linhas[(documento_cnpj, referencia, int(r["VERSAO"]))] = {
                    "cnpj": documento_cnpj,
                    "data_referencia": referencia,
                    "versao": int(r["VERSAO"]),
                    "acoes_ordinarias": _inteiro(r["QT_ACAO_ORDIN_CAP_INTEGR"]),
                    "acoes_preferenciais": _inteiro(r["QT_ACAO_PREF_CAP_INTEGR"]),
                    "acoes_total": _inteiro(r["QT_ACAO_TOTAL_CAP_INTEGR"]),
                    "tesouraria_total": _inteiro(r["QT_ACAO_TOTAL_TESOURO"]),
                }
    return list(linhas.values())


_GRAVAR_COMPOSICAO = """
INSERT INTO mercado.composicao_capital AS x
    (documento_id, acoes_ordinarias, acoes_preferenciais, acoes_total, tesouraria_total)
SELECT d.id, :acoes_ordinarias, :acoes_preferenciais, :acoes_total, :tesouraria_total
FROM mercado.documento d
WHERE d.cnpj = :cnpj AND d.tipo = :tipo AND d.data_referencia = :data_referencia
  AND d.versao = :versao
ON CONFLICT (documento_id) DO UPDATE SET
    acoes_ordinarias = EXCLUDED.acoes_ordinarias,
    acoes_preferenciais = EXCLUDED.acoes_preferenciais,
    acoes_total = EXCLUDED.acoes_total,
    tesouraria_total = EXCLUDED.tesouraria_total
"""


def gravar_composicao(conn: sa.Connection, conteudo: bytes, tipo: str) -> int:
    linhas = interpretar_composicao(conteudo, tipo)
    if linhas:
        conn.execute(sa.text(_GRAVAR_COMPOSICAO), [{**linha, "tipo": tipo} for linha in linhas])
    return len(linhas)


def com_acao(conn: sa.Connection) -> set[str]:
    return set(conn.execute(sa.text("SELECT DISTINCT cnpj FROM mercado.emissor")).scalars())


def processador(tipo: str) -> Callable[[sa.Connection, bytes, int], tuple[int, int, int]]:
    def processar(conn: sa.Connection, conteudo: bytes, coleta_id: int) -> tuple[int, int, int]:
        leitura = interpretar(conteudo, tipo, com_acao(conn))
        gravadas, sem_documento = gravar(conn, leitura, tipo, coleta_id)
        gravar_composicao(conn, conteudo, tipo)
        return leitura.lidas, gravadas, len(leitura.rejeitadas) + sem_documento

    return processar
