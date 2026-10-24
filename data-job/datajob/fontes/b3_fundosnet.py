from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import sqlalchemy as sa

from datajob.erros import ArquivoInvalido

FONTE = "b3_fundosnet"
ORIGEM = "fundosnet"

_BASE = "https://fnet.bmfbovespa.com.br/fnet/publico/"
_POR_PAGINA = 200
_TIPOS = {"Rendimento": "RENDIMENTO", "Amortizacao": "AMORTIZACAO"}


def url_da_lista(inicio: int) -> str:
    return (
        f"{_BASE}pesquisarGerenciadorDocumentosDados?d=1&s={inicio}&l={_POR_PAGINA}"
        "&o%5B0%5D%5BdataEntrega%5D=asc&tipoFundo=1&idCategoriaDocumento=14"
        "&idTipoDocumento=41&idEspecieDocumento=0"
    )


def url_do_documento(documento_id: int) -> str:
    return f"{_BASE}downloadDocumento?id={documento_id}"


def nome(documento_id: int) -> str:
    return f"fundosnet_{documento_id}.xml"


def ativos(baixar: Callable[[str], bytes]) -> list[int]:
    ids, inicio, total = [], 0, 1
    while inicio < total:
        pagina = json.loads(baixar(url_da_lista(inicio)))
        total = pagina["recordsTotal"]
        if not pagina["data"]:
            raise ArquivoInvalido(f"O FundosNet listou {inicio} de {total} avisos e parou.")
        ids += [d["id"] for d in pagina["data"] if d.get("situacaoDocumento") == "A"]
        inicio += _POR_PAGINA
    return ids


def _texto(no: ET.Element, *tags: str) -> str:
    for tag in tags:
        achado = no.findtext(tag)
        if achado and achado.strip():
            return achado.strip()
    return ""


def _data(texto: str) -> date | None:
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            pass
    return None


def interpretar(conteudo: bytes) -> tuple[list[dict], list[tuple[str, str]]]:
    try:
        raiz = ET.fromstring(conteudo)
    except ET.ParseError as e:
        raise ArquivoInvalido("O aviso do FundosNet não é um XML legível.") from e

    informe = raiz.find("InformeRendimentos")
    if informe is None:
        return [], []
    # Até 2023 o aviso tinha uma cota só, com o ISIN nos dados gerais; depois, um bloco por cota.
    blocos = informe.findall("Provento") or [informe]
    isin_geral = _texto(raiz, "DadosGerais/CodISINCota")

    proventos, rejeitados = [], []
    for bloco in blocos:
        isin = (_texto(bloco, "CodISIN") or isin_geral).upper()
        for tag, tipo in _TIPOS.items():
            for no in bloco.findall(tag):
                bruto = _texto(no, "ValorProvento", "ValorProventoCota")
                if not bruto:
                    continue
                try:
                    valor = Decimal(bruto.replace(",", "."))
                except InvalidOperation:
                    valor = None
                data_com = _data(_texto(no, "DataBase"))
                if valor is None or data_com is None or len(isin) != 12:
                    rejeitados.append((f"{isin} {tipo} {data_com}", "provento ilegível"))
                    continue
                if valor <= 0:
                    continue
                proventos.append(
                    {
                        "isin": isin,
                        "data_com": data_com,
                        "tipo": tipo,
                        "valor": valor,
                        "data_aprovacao": _data(_texto(no, "DataAprovacao")),
                        "data_pagamento": _data(_texto(no, "DataPagamento")),
                    }
                )
    return proventos, rejeitados


_CLASSE_DO_ISIN = sa.text(
    "SELECT isin, substring(especie FROM '^([A-Z0-9]+)') FROM mercado.ativo WHERE isin = ANY(:isins)"
)

_DO_MESMO_AVISO = sa.text(
    """
    DELETE FROM mercado.provento WHERE origem = :origem AND coleta_id IN (
        SELECT id FROM mercado.coleta WHERE fonte = :fonte
          AND arquivo = (SELECT arquivo FROM mercado.coleta WHERE id = :coleta_id))
    """
)


def processar(conn: sa.Connection, conteudo: bytes, coleta_id: int) -> tuple[int, int, int]:
    proventos, rejeitados = interpretar(conteudo)
    classes = dict(
        conn.execute(_CLASSE_DO_ISIN, {"isins": list({p["isin"] for p in proventos})}).all()
    )
    linhas = [
        {
            **{k: v for k, v in p.items() if k != "isin"},
            "emissor": p["isin"][2:6],
            "classe": classes[p["isin"]],
            "origem": ORIGEM,
            "coleta_id": coleta_id,
        }
        for p in proventos
        if p["isin"] in classes
    ]

    conn.execute(_DO_MESMO_AVISO, {"origem": ORIGEM, "fonte": FONTE, "coleta_id": coleta_id})
    if linhas:
        conn.execute(
            sa.text(
                "INSERT INTO mercado.provento (emissor, classe, data_com, tipo, valor, "
                "data_aprovacao, data_pagamento, origem, coleta_id) VALUES (:emissor, :classe, "
                ":data_com, :tipo, :valor, :data_aprovacao, :data_pagamento, :origem, :coleta_id)"
            ),
            linhas,
        )
    if rejeitados:
        conn.execute(
            sa.text(
                "INSERT INTO mercado.quarentena (coleta_id, chave, motivo, conteudo) "
                "VALUES (:coleta_id, :chave, :motivo, :chave)"
            ),
            [{"coleta_id": coleta_id, "chave": c, "motivo": m} for c, m in rejeitados],
        )
    return len(proventos) + len(rejeitados), len(linhas), len(rejeitados)


_INATIVOS = sa.text(
    """
    DELETE FROM mercado.provento WHERE origem = :origem AND coleta_id IN (
        SELECT id FROM mercado.coleta WHERE fonte = :fonte AND arquivo <> ALL(:ativos))
    """
)

# O rendimento recente vem da B3 e do FundosNet: fica o da B3, e o aviso repetido conta uma vez.
_REPETIDOS = sa.text(
    """
    DELETE FROM mercado.provento f WHERE f.origem = :origem AND (
        EXISTS (
            SELECT 1 FROM mercado.provento b
            WHERE b.origem LIKE 'b3_%' AND b.emissor = f.emissor AND b.classe = f.classe
              AND b.data_com = f.data_com AND abs(b.valor - f.valor) <= b.valor / 100)
        OR EXISTS (
            SELECT 1 FROM mercado.provento o
            WHERE o.origem = :origem AND o.emissor = f.emissor AND o.classe = f.classe
              AND o.data_com = f.data_com AND o.tipo = f.tipo AND o.valor = f.valor
              AND o.id < f.id))
    """
)


def conciliar(conn: sa.Connection, ativos: list[int]) -> int:
    inativos = conn.execute(
        _INATIVOS, {"origem": ORIGEM, "fonte": FONTE, "ativos": [nome(i) for i in ativos]}
    ).rowcount
    return inativos + conn.execute(_REPETIDOS, {"origem": ORIGEM}).rowcount
