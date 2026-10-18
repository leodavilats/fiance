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
EXATO = Decimal("0.01")
MAIOR_FATOR = 1000
JANELA_ANTES = timedelta(days=120)
JANELA_DEPOIS = timedelta(days=10)
FRE_ANTES = timedelta(days=200)
FRE_DEPOIS = timedelta(days=30)
# Com documento no IPE, o FRE só corrobora: a emissão junto do desdobramento e o registro tardio
# da aprovação (MGLU3 em 2017 e 2019) cabem.
FRE_DEPOIS_COM_DOCUMENTO = timedelta(days=120)
FOLGA_DO_FRE_COM_DOCUMENTO = Decimal("0.15")
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
    mudancas_fre: tuple = ()


def _perto(razao: Decimal, fator: Decimal, folga: Decimal = TOLERANCIA) -> bool:
    return abs(razao / fator - 1) <= folga


def fator_comum(
    razao_preco: Decimal, razao_acoes: Decimal, folga_acoes: Decimal = TOLERANCIA
) -> Decimal | None:
    candidatos = FATORES if razao_preco >= 1 else tuple(1 / f for f in FATORES)
    aceitos = [
        f for f in candidatos if _perto(razao_preco, f) and _perto(razao_acoes, f, folga_acoes)
    ]
    return aceitos[0] if len(aceitos) == 1 else None


def fator_exato(razao: Decimal) -> Decimal | None:
    if razao <= 0:
        return None
    n = razao if razao >= 1 else 1 / razao
    inteiro = n.to_integral_value()
    if not 2 <= inteiro <= MAIOR_FATOR or abs(n / inteiro - 1) > EXATO:
        return None
    return inteiro if razao >= 1 else 1 / inteiro


def fator_pelo_fre(
    razao_preco: Decimal, razao_acoes: Decimal, folga_acoes: Decimal = TOLERANCIA
) -> Decimal | None:
    comum = fator_comum(razao_preco, razao_acoes, folga_acoes)
    if comum is not None:
        return comum
    exato = fator_exato(razao_acoes)
    return exato if exato is not None and _perto(razao_preco, exato) else None


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

# O histórico do capital integralizado no FRE: a quantidade de ações depois de cada aprovação.
_MUDANCAS_DO_FRE = sa.text(
    """
    WITH ultima AS (
        SELECT DISTINCT ON (cnpj, data_aprovacao) cnpj, data_aprovacao, acoes_total
        FROM mercado.capital_social
        WHERE cnpj = ANY(:cnpjs)
        ORDER BY cnpj, data_aprovacao, data_referencia DESC, versao DESC
    )
    SELECT cnpj, data_aprovacao, acoes_total,
        lag(acoes_total) OVER (PARTITION BY cnpj ORDER BY data_aprovacao) AS anterior
    FROM ultima
    """
)

_DOCUMENTOS = sa.text(
    "SELECT cnpj, data_entrega, assunto, protocolo FROM mercado.ipe_documento "
    "WHERE cnpj = ANY(:cnpjs)"
)


def _pelo_fre(s: Salto, razao_preco: Decimal, documentos: list, inicio_do_ipe: date | None):
    com_ipe = inicio_do_ipe is not None and s.data - JANELA_ANTES >= inicio_do_ipe
    depois_do_salto = FRE_DEPOIS_COM_DOCUMENTO if com_ipe else FRE_DEPOIS
    folga = FOLGA_DO_FRE_COM_DOCUMENTO if com_ipe else TOLERANCIA
    for aprovacao, antes, depois in s.mudancas_fre:
        if not (s.data - FRE_ANTES <= aprovacao <= s.data + depois_do_salto) or not antes:
            continue
        multiplicador = fator_pelo_fre(razao_preco, Decimal(depois) / Decimal(antes), folga)
        if multiplicador is None:
            continue
        if com_ipe:
            achado = evidencia(multiplicador, documentos, s.data)
            if achado is not None:
                return multiplicador, achado
            continue
        # Antes do IPE existir, o FRE e o preço são as duas provas que há.
        return multiplicador, (
            f"FRE {aprovacao:%Y-%m-%d}",
            f"Capital social do FRE: {antes} para {depois} ações",
        )
    return None


def candidatos(
    saltos: list[Salto], documentos: dict[str, list], inicio_do_ipe: date | None = None
) -> list[dict]:
    inferidos = []
    for s in saltos:
        if not (s.fechamento_anterior and s.abertura):
            continue
        razao_preco = Decimal(s.fechamento_anterior) / Decimal(s.abertura)
        achado = None
        if s.acoes_antes and s.acoes_depois:
            multiplicador = fator_comum(
                razao_preco, Decimal(s.acoes_depois) / Decimal(s.acoes_antes)
            )
            if multiplicador is not None:
                documento = evidencia(multiplicador, documentos.get(s.cnpj, []), s.data)
                achado = (multiplicador, documento) if documento else None
        if achado is None:
            achado = _pelo_fre(s, razao_preco, documentos.get(s.cnpj, []), inicio_do_ipe)
        if achado is None:
            continue
        multiplicador, achado = achado
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


# FII não está no IPE: a segunda prova é a quantidade de cotas do informe mensal da CVM, do mês
# anterior à data-com para o mês do salto.
_SALTOS_DE_FII = sa.text(
    """
    WITH s AS (
        SELECT s.emissor, s.classe, s.data, s.data - s.dias_desde_anterior AS data_anterior,
            (SELECT p.fechamento FROM mercado.serie_fundo p
              WHERE p.emissor = s.emissor AND p.classe = s.classe AND p.data < s.data
              ORDER BY p.data DESC LIMIT 1) AS fechamento_anterior,
            c.abertura / c.fator_cotacao AS abertura
        FROM mercado.serie_fundo s
        JOIN mercado.cotacao c ON c.isin = s.isin AND c.data = s.data
        WHERE s.salto_sem_evento AND s.dias_desde_anterior <= 30 AND s.tipo_ativo = 'fii'
    ),
    informe AS (
        SELECT s.*,
            (SELECT f FROM mercado.fii_mensal f WHERE f.emissor = s.emissor AND f.classe = s.classe
              AND f.referencia < date_trunc('month', s.data_anterior)
              ORDER BY f.referencia DESC LIMIT 1) AS antes,
            (SELECT f FROM mercado.fii_mensal f WHERE f.emissor = s.emissor AND f.classe = s.classe
              AND f.referencia >= date_trunc('month', s.data)
              ORDER BY f.referencia LIMIT 1) AS depois
        FROM s
    )
    SELECT emissor, classe, data, data_anterior, fechamento_anterior, abertura,
        (depois).cnpj AS cnpj, (antes).referencia AS referencia_antes,
        (antes).cotas_emitidas AS cotas_antes, (depois).referencia AS referencia_depois,
        (depois).cotas_emitidas AS cotas_depois
    FROM informe
    WHERE (antes).cotas_emitidas > 0 AND (depois).cotas_emitidas > 0
    """
)
MESES_ENTRE_INFORMES = 3


def candidatos_de_fii(linhas: list) -> list[dict]:
    inferidos = []
    for s in linhas:
        if not (s.fechamento_anterior and s.abertura and s.cnpj):
            continue
        meses = (s.referencia_depois.year - s.referencia_antes.year) * 12 + (
            s.referencia_depois.month - s.referencia_antes.month
        )
        if meses > MESES_ENTRE_INFORMES:
            continue
        razao_preco = Decimal(s.fechamento_anterior) / Decimal(s.abertura)
        razao_cotas = Decimal(s.cotas_depois) / Decimal(s.cotas_antes)
        multiplicador = fator_pelo_fre(razao_preco, razao_cotas)
        if multiplicador is None:
            continue
        inferidos.append(
            {
                "cnpj": s.cnpj,
                "classe": s.classe,
                "data_com": s.data_anterior,
                "multiplicador": multiplicador,
                "razao_observada": razao_preco,
                "protocolo": f"Informe FII {s.referencia_antes:%Y-%m} a {s.referencia_depois:%Y-%m}",
                "assunto": f"Cotas emitidas: {s.cotas_antes} para {s.cotas_depois}",
            }
        )
    return inferidos


def _de_acoes(conn: sa.Connection) -> list[dict]:
    linhas = list(conn.execute(_SALTOS))
    if not linhas:
        return []
    cnpjs = sorted({linha.cnpj for linha in linhas})
    documentos: dict[str, list] = {}
    for documento, entrega, assunto, protocolo in conn.execute(_DOCUMENTOS, {"cnpjs": cnpjs}):
        documentos.setdefault(documento, []).append((entrega, assunto, protocolo))
    fre: dict[str, list] = {}
    for cnpj, aprovacao, acoes, anterior in conn.execute(_MUDANCAS_DO_FRE, {"cnpjs": cnpjs}):
        fre.setdefault(cnpj, []).append((aprovacao, anterior, acoes))
    saltos = [Salto(*linha, mudancas_fre=tuple(fre.get(linha.cnpj, ()))) for linha in linhas]
    inicio_do_ipe = conn.execute(
        sa.text("SELECT min(data_entrega) FROM mercado.ipe_documento")
    ).scalar()
    return candidatos(saltos, documentos, inicio_do_ipe)


def inferir(conn: sa.Connection) -> int:
    novos = 0
    for inferido in _de_acoes(conn) + candidatos_de_fii(list(conn.execute(_SALTOS_DE_FII))):
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
