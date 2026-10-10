from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

import sqlalchemy as sa

# Só os fatores que aparecem em desdobramento e grupamento na B3; com 7, 9 ou 12 na lista, a Gafisa
# de 2022 (10 para 1 junto de aumento de capital) seria lida como 9 para 1.
FATORES = tuple(
    Decimal(f) for f in (2, 3, 4, 5, 6, 8, 10, 20, 25, 50, 100, 200, 1000)
)  # fmt: skip
TOLERANCIA = Decimal("0.10")
JANELA_ANTES = timedelta(days=120)
JANELA_DEPOIS = timedelta(days=10)
MAIS_ACOES = re.compile(r"desdobr|bonifica|split", re.IGNORECASE)
MENOS_ACOES = re.compile(r"grupam|inplit|reverse", re.IGNORECASE)


@dataclass(frozen=True)
class Salto:
    cnpj: str
    classe: str
    data: date
    data_anterior: date
    fechamento_anterior: Decimal | None
    abertura: Decimal | None
    acoes_antes: int | None
    acoes_depois: int | None


def _perto(razao: Decimal, fator: Decimal) -> bool:
    return abs(razao / fator - 1) <= TOLERANCIA


def fator_comum(razao_preco: Decimal, razao_acoes: Decimal) -> Decimal | None:
    candidatos = FATORES if razao_preco >= 1 else tuple(1 / f for f in FATORES)
    aceitos = [f for f in candidatos if _perto(razao_preco, f) and _perto(razao_acoes, f)]
    return aceitos[0] if len(aceitos) == 1 else None


def evidencia(multiplicador: Decimal, documentos: list[tuple[date, str, str]], dia: date):
    padrao = MAIS_ACOES if multiplicador > 1 else MENOS_ACOES
    for entrega, assunto, protocolo in sorted(documentos):
        if dia - JANELA_ANTES <= entrega <= dia + JANELA_DEPOIS and padrao.search(assunto):
            return protocolo, assunto
    return None


_SALTOS = sa.text(
    """
    WITH s AS (
        SELECT s.cnpj, s.classe, s.data, s.data - s.dias_desde_anterior AS data_anterior,
            (SELECT p.fechamento FROM mercado.serie_papel p
              WHERE p.cnpj = s.cnpj AND p.classe = s.classe AND p.data < s.data
              ORDER BY p.data DESC LIMIT 1) AS fechamento_anterior,
            c.abertura / c.fator_cotacao AS abertura
        FROM mercado.serie_papel s
        JOIN mercado.cotacao c ON c.isin = s.isin AND c.data = s.data
        WHERE s.salto_sem_evento AND s.dias_desde_anterior <= 30
    ),
    acoes AS (
        SELECT d.cnpj, d.data_referencia, max(k.acoes_total) AS acoes
        FROM mercado.composicao_capital k
        JOIN mercado.documento d ON d.id = k.documento_id
        WHERE k.acoes_total > 0
        GROUP BY d.cnpj, d.data_referencia
    )
    SELECT s.*,
        (SELECT a.acoes FROM acoes a WHERE a.cnpj = s.cnpj AND a.data_referencia < s.data
          ORDER BY a.data_referencia DESC LIMIT 1) AS acoes_antes,
        (SELECT a.acoes FROM acoes a WHERE a.cnpj = s.cnpj AND a.data_referencia >= s.data
          ORDER BY a.data_referencia LIMIT 1) AS acoes_depois
    FROM s
    """
)

_DOCUMENTOS = sa.text(
    "SELECT cnpj, data_entrega, assunto, protocolo FROM mercado.ipe_documento "
    "WHERE cnpj = ANY(:cnpjs)"
)


def candidatos(saltos: list[Salto], documentos: dict[str, list]) -> list[dict]:
    inferidos = []
    for s in saltos:
        if not (s.fechamento_anterior and s.abertura and s.acoes_antes and s.acoes_depois):
            continue
        razao_preco = Decimal(s.fechamento_anterior) / Decimal(s.abertura)
        razao_acoes = Decimal(s.acoes_depois) / Decimal(s.acoes_antes)
        multiplicador = fator_comum(razao_preco, razao_acoes)
        if multiplicador is None:
            continue
        achado = evidencia(multiplicador, documentos.get(s.cnpj, []), s.data)
        if achado is None:
            continue
        inferidos.append(
            {
                "cnpj": s.cnpj,
                "classe": s.classe,
                "data_com": s.data_anterior,
                "multiplicador": multiplicador,
                "razao_observada": razao_preco,
                "protocolo": achado[0],
                "assunto": achado[1],
            }
        )
    return inferidos


def inferir(conn: sa.Connection) -> int:
    saltos = [Salto(*linha) for linha in conn.execute(_SALTOS)]
    if not saltos:
        return 0
    documentos: dict[str, list] = {}
    for documento, entrega, assunto, protocolo in conn.execute(
        _DOCUMENTOS, {"cnpjs": sorted({s.cnpj for s in saltos})}
    ):
        documentos.setdefault(documento, []).append((entrega, assunto, protocolo))

    novos = 0
    for inferido in candidatos(saltos, documentos):
        novos += conn.execute(
            sa.text(
                "INSERT INTO mercado.evento_inferido (cnpj, classe, data_com, multiplicador, "
                "razao_observada, protocolo, assunto) VALUES (:cnpj, :classe, :data_com, "
                ":multiplicador, :razao_observada, :protocolo, :assunto) "
                "ON CONFLICT (cnpj, classe, data_com) DO NOTHING"
            ),
            inferido,
        ).rowcount
    return novos
