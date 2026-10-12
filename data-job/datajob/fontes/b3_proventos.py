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


def baixar_emissor(
    emissor: str, baixar: Callable[[str], bytes], com_historico: bool = True
) -> bytes:
    resposta = json.loads(baixar(url_do_complemento(emissor)) or b"null")
    complemento = resposta[0] if isinstance(resposta, list) and resposta else {}
    nome = (complemento.get("tradingName") or "").strip()

    proventos: list[dict] = []
    for tentativa in nomes_possiveis(nome) if com_historico else []:
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
        "recentes": complemento.get("cashDividends") or [],
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


def interpretar_recentes(pacote: dict) -> list[dict]:
    recentes = []
    for p in pacote.get("recentes") or []:
        data_com, valor = _data(p.get("lastDatePrior")), _numero(p.get("rate"))
        if data_com is None or valor is None or not p.get("isinCode"):
            continue
        recentes.append(
            {
                "emissor": pacote["emissor"],
                "isin": p["isinCode"],
                "data_com": data_com,
                "tipo": p.get("label") or "",
                "valor": valor,
                "data_aprovacao": _data(p.get("approvedOn")),
                "data_pagamento": _data(p.get("paymentDate")),
            }
        )
    return recentes


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


_CLASSE_DO_ISIN = sa.text(
    "SELECT isin, substring(especie FROM '^([A-Z0-9]+)') FROM mercado.ativo WHERE isin = ANY(:isins)"
)

# A B3 só dá o histórico de proventos de companhia; de fundo e BDR, só os últimos meses. Esses se
# acumulam a cada coleta, e não substituem o que já foi guardado.
_ACUMULAR = sa.text(
    """
    INSERT INTO mercado.provento (emissor, classe, data_com, tipo, valor, data_aprovacao,
        data_pagamento, origem, coleta_id)
    SELECT :emissor, :classe, :data_com, :tipo, :valor, :data_aprovacao, :data_pagamento,
        'b3_recente', :coleta_id
    WHERE NOT EXISTS (
        SELECT 1 FROM mercado.provento
        WHERE emissor = :emissor AND classe = :classe AND data_com = :data_com AND tipo = :tipo
          AND valor = :valor)
    """
)


# O histórico da B3 não traz a data de pagamento; os recentes trazem, e ela vale para os dois.
_DATA_DE_PAGAMENTO = sa.text(
    """
    UPDATE mercado.provento SET data_pagamento = :data_pagamento
    WHERE emissor = :emissor AND classe = :classe AND data_com = :data_com AND valor = :valor
      AND origem LIKE 'b3_%' AND data_pagamento IS DISTINCT FROM :data_pagamento
    """
)


def _recentes_com_classe(conn: sa.Connection, pacote: dict) -> list[dict]:
    recentes = interpretar_recentes(pacote)
    if not recentes:
        return []
    classes = dict(conn.execute(_CLASSE_DO_ISIN, {"isins": [r["isin"] for r in recentes]}).all())
    return [
        {**{k: v for k, v in r.items() if k != "isin"}, "classe": classes[r["isin"]]}
        for r in recentes
        if r["isin"] in classes
    ]


def _acumular_recentes(conn: sa.Connection, recentes: list[dict], coleta_id: int) -> int:
    return sum(conn.execute(_ACUMULAR, {**r, "coleta_id": coleta_id}).rowcount for r in recentes)


def _datas_de_pagamento(conn: sa.Connection, recentes: list[dict]) -> None:
    for r in recentes:
        if r["data_pagamento"] is not None:
            conn.execute(_DATA_DE_PAGAMENTO, r)


def processar(conn: sa.Connection, conteudo: bytes, coleta_id: int) -> tuple[int, int, int]:
    emissor, proventos, eventos, rejeitados = interpretar(conteudo)
    validar(conn, eventos)

    conn.execute(sa.text("DELETE FROM mercado.evento WHERE emissor = :e"), {"e": emissor})
    acumulados = 0
    recentes = _recentes_com_classe(conn, json.loads(conteudo))
    if not proventos:
        acumulados = _acumular_recentes(conn, recentes, coleta_id)
    else:
        conn.execute(
            sa.text("DELETE FROM mercado.provento WHERE emissor = :e AND origem LIKE 'b3_%'"),
            {"e": emissor},
        )
        conn.execute(
            sa.text(
                "INSERT INTO mercado.provento (emissor, classe, data_com, tipo, valor, "
                "data_aprovacao, preco_vespera, origem, coleta_id) VALUES (:emissor, :classe, "
                ":data_com, :tipo, :valor, :data_aprovacao, :preco_vespera, 'b3_historico', "
                ":coleta_id)"
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

    _datas_de_pagamento(conn, recentes)

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
        len(proventos) + len(eventos) + acumulados,
        len(quarentena),
    )
