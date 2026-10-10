from __future__ import annotations

import base64
import json
from collections import defaultdict
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import sqlalchemy as sa

from datajob.erros import ArquivoInvalido

FONTE = "b3_proventos"

_BASE = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/"
_POR_PAGINA = 120

AJUSTAM = {"DESDOBRAMENTO", "GRUPAMENTO", "BONIFICACAO"}
_TOLERANCIA = Decimal("0.12")


def _url(metodo: str, consulta: dict) -> str:
    return _BASE + metodo + "/" + base64.b64encode(json.dumps(consulta).encode()).decode()


def url_do_complemento(emissor: str) -> str:
    return _url("GetListedSupplementCompany", {"issuingCompany": emissor, "language": "pt-br"})


def url_dos_proventos(nome_pregao: str, pagina: int) -> str:
    consulta = {
        "language": "pt-br",
        "pageNumber": pagina,
        "pageSize": _POR_PAGINA,
        "tradingName": nome_pregao,
    }
    return _url("GetListedCashDividends", consulta)


def nomes_possiveis(nome_pregao: str) -> list[str]:
    nome = nome_pregao.strip()
    variantes = [nome, nome.replace("S/A", "SA"), nome.replace("/", "")]
    return list(dict.fromkeys(v for v in variantes if v))


def baixar_emissor(emissor: str, baixar: Callable[[str], bytes]) -> bytes:
    resposta = json.loads(baixar(url_do_complemento(emissor)) or b"null")
    complemento = resposta[0] if isinstance(resposta, list) and resposta else {}
    nome = (complemento.get("tradingName") or "").strip()

    proventos: list[dict] = []
    for tentativa in nomes_possiveis(nome):
        pagina, paginas = 1, 1
        while pagina <= paginas:
            dados = json.loads(baixar(url_dos_proventos(tentativa, pagina)))
            paginas = dados["page"]["totalPages"]
            proventos += dados.get("results") or []
            pagina += 1
        if proventos:
            break

    pacote = {
        "emissor": emissor,
        "nome_pregao": nome,
        "eventos": complemento.get("stockDividends") or [],
        "proventos": proventos,
    }
    return json.dumps(pacote, ensure_ascii=False, sort_keys=True).encode()


def _data(texto: str | None) -> date | None:
    try:
        return datetime.strptime(texto or "", "%d/%m/%Y").date()
    except ValueError:
        return None


def _numero(texto: str | None) -> Decimal | None:
    try:
        return Decimal((texto or "").replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def multiplicador(tipo: str, fator: Decimal) -> Decimal | None:
    if tipo == "GRUPAMENTO":
        return fator
    if tipo in ("DESDOBRAMENTO", "BONIFICACAO"):
        return 1 + fator / 100
    return None


def interpretar(conteudo: bytes) -> tuple[str, list[dict], list[dict], list[tuple[str, str]]]:
    try:
        pacote = json.loads(conteudo)
        emissor = pacote["emissor"]
    except (ValueError, KeyError, TypeError) as e:
        raise ArquivoInvalido("O pacote de proventos da B3 está ilegível.") from e

    proventos, eventos, rejeitados = [], [], []
    for p in pacote.get("proventos") or []:
        data_com, valor = _data(p.get("lastDatePriorEx")), _numero(p.get("valueCash"))
        por = _numero(p.get("quotedPerShares")) or Decimal(1)
        if data_com is None or valor is None or por <= 0 or not p.get("typeStock"):
            rejeitados.append((f"{emissor} {p}", "provento ilegível"))
            continue
        proventos.append(
            {
                "emissor": emissor,
                "classe": p["typeStock"],
                "data_com": data_com,
                "tipo": p.get("corporateAction") or "",
                "valor": valor / por,
                "data_aprovacao": _data(p.get("dateApproval")),
                "preco_vespera": _numero(p.get("closingPricePriorExDate")),
            }
        )

    for e in pacote.get("eventos") or []:
        data_com, fator = _data(e.get("lastDatePrior")), _numero(e.get("factor"))
        if data_com is None or fator is None or not e.get("isinCode"):
            rejeitados.append((f"{emissor} {e}", "evento ilegível"))
            continue
        eventos.append(
            {
                "emissor": emissor,
                "isin": e["isinCode"],
                "data_com": data_com,
                "tipo": e.get("label") or "",
                "fator": fator,
                "multiplicador": multiplicador(e.get("label") or "", fator),
                "data_aprovacao": _data(e.get("approvedOn")),
            }
        )
    return emissor, proventos, eventos, rejeitados


_PRECO_EM_VOLTA = sa.text(
    """
    SELECT
      (SELECT fechamento / fator_cotacao FROM mercado.cotacao
        WHERE isin = :isin AND data <= :data ORDER BY data DESC LIMIT 1),
      (SELECT abertura / fator_cotacao FROM mercado.cotacao
        WHERE isin = :isin AND data > :data ORDER BY data LIMIT 1)
    """
)


def validar(conn: sa.Connection, eventos: list[dict]) -> None:
    grupos: dict[tuple, list[dict]] = defaultdict(list)
    for e in eventos:
        if e["multiplicador"] is None:
            e["status"], e["razao_observada"] = "nao_ajusta", None
        else:
            grupos[(e["isin"], e["data_com"])].append(e)

    for (isin, data_com), grupo in grupos.items():
        tipos_vistos, combinado = set(), Decimal(1)
        for e in grupo:
            if e["tipo"] not in tipos_vistos:
                combinado *= e["multiplicador"]
                tipos_vistos.add(e["tipo"])
        antes, depois = conn.execute(_PRECO_EM_VOLTA, {"isin": isin, "data": data_com}).one()
        if not antes or not depois:
            status, observada = "sem_preco", None
        else:
            observada = Decimal(antes) / Decimal(depois)
            confere = abs(observada / combinado - 1) <= _TOLERANCIA
            status = "confirmado" if confere else "divergente"
        for e in grupo:
            e["status"], e["razao_observada"] = status, observada


def processar(conn: sa.Connection, conteudo: bytes, coleta_id: int) -> tuple[int, int, int]:
    emissor, proventos, eventos, rejeitados = interpretar(conteudo)
    validar(conn, eventos)

    conn.execute(sa.text("DELETE FROM mercado.provento WHERE emissor = :e"), {"e": emissor})
    conn.execute(sa.text("DELETE FROM mercado.evento WHERE emissor = :e"), {"e": emissor})
    if proventos:
        conn.execute(
            sa.text(
                "INSERT INTO mercado.provento (emissor, classe, data_com, tipo, valor, "
                "data_aprovacao, preco_vespera, coleta_id) VALUES (:emissor, :classe, :data_com, "
                ":tipo, :valor, :data_aprovacao, :preco_vespera, :coleta_id)"
            ),
            [{**p, "coleta_id": coleta_id} for p in proventos],
        )
    if eventos:
        conn.execute(
            sa.text(
                "INSERT INTO mercado.evento (emissor, isin, data_com, tipo, fator, multiplicador, "
                "data_aprovacao, status, razao_observada, coleta_id) VALUES (:emissor, :isin, "
                ":data_com, :tipo, :fator, :multiplicador, :data_aprovacao, :status, "
                ":razao_observada, :coleta_id)"
            ),
            [{**e, "coleta_id": coleta_id} for e in eventos],
        )

    quarentena = [(c, m, c) for c, m in rejeitados] + [
        (f"{e['isin']} {e['data_com']} {e['tipo']}", "evento não confirmado pelo preço", str(e))
        for e in eventos
        if e["status"] == "divergente"
    ]
    if quarentena:
        conn.execute(
            sa.text(
                "INSERT INTO mercado.quarentena (coleta_id, chave, motivo, conteudo) "
                "VALUES (:coleta_id, :chave, :motivo, :conteudo)"
            ),
            [
                {"coleta_id": coleta_id, "chave": c, "motivo": m, "conteudo": t}
                for c, m, t in quarentena
            ],
        )
    return (
        len(proventos) + len(eventos) + len(rejeitados),
        len(proventos) + len(eventos),
        len(quarentena),
    )
