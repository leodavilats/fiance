from __future__ import annotations

import time
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from api.alertas import avaliar as avaliar_alertas

_BRT = ZoneInfo("America/Sao_Paulo")


def _linhas(conn: sa.Connection, sql: str, **parametros) -> list[dict]:
    return [dict(r._mapping) for r in conn.execute(sa.text(sql), parametros)]


def coleta(conn: sa.Connection) -> dict:
    return {
        "ultimas": _linhas(
            conn,
            """
            SELECT DISTINCT ON (fonte) fonte, arquivo, status, iniciada_em, terminada_em,
                linhas_lidas, linhas_gravadas, linhas_quarentena, erro
            FROM mercado.coleta ORDER BY fonte, iniciada_em DESC
            """,
        ),
        "falhas_7_dias": _linhas(
            conn,
            """
            SELECT fonte, count(*) AS falhas, max(iniciada_em) AS ultima
            FROM mercado.coleta
            WHERE status = 'falhou' AND iniciada_em > now() - interval '7 days'
            GROUP BY fonte ORDER BY fonte
            """,
        ),
        "quarentena": _linhas(
            conn,
            "SELECT motivo, count(*) AS linhas FROM mercado.quarentena GROUP BY motivo "
            "ORDER BY linhas DESC LIMIT 15",
        ),
        "atualidade": _linhas(
            conn,
            """
            SELECT 'cotação' AS base, max(data)::text AS ate FROM mercado.cotacao
            UNION ALL SELECT 'série ajustada', max(data)::text FROM mercado.serie_papel
            UNION ALL SELECT 'série de fundos e BDRs', max(data)::text FROM mercado.serie_fundo
            UNION ALL SELECT 'Tesouro Direto', max(data)::text FROM mercado.tesouro
            UNION ALL SELECT 'PTAX', max(data)::text FROM mercado.indicador WHERE serie = 1
            UNION ALL SELECT 'DFP (entrega)', max(data_entrega)::text FROM mercado.documento
                WHERE tipo = 'DFP'
            UNION ALL SELECT 'ITR (entrega)', max(data_entrega)::text FROM mercado.documento
                WHERE tipo = 'ITR'
            UNION ALL SELECT 'provento (data-com)', max(data_com)::text FROM mercado.provento
            UNION ALL SELECT 'CDI', max(data)::text FROM mercado.indicador WHERE serie = 12
            UNION ALL SELECT 'IPCA', max(data)::text FROM mercado.indicador WHERE serie = 433
            """,
        ),
    }


_PAPEIS: dict = {"quando": 0.0, "lista": []}
_VALIDADE_DOS_PAPEIS = 3600


def papeis(conn: sa.Connection) -> list[dict]:
    if time.monotonic() - _PAPEIS["quando"] > _VALIDADE_DOS_PAPEIS or not _PAPEIS["lista"]:
        _PAPEIS["lista"] = _linhas(
            conn,
            """
            SELECT p.cnpj, p.classe, p.codigo, p.ultimo_pregao, e.razao_social, e.setor
            FROM (
                SELECT DISTINCT ON (cnpj, classe) cnpj, classe, codigo, data AS ultimo_pregao
                FROM mercado.serie_papel ORDER BY cnpj, classe, data DESC
            ) p
            LEFT JOIN mercado.empresa e ON e.cnpj = p.cnpj
            ORDER BY p.codigo
            """,
        )
        _PAPEIS["quando"] = time.monotonic()
    return _PAPEIS["lista"]


def papel(conn: sa.Connection, cnpj: str, classe: str) -> dict | None:
    serie = _linhas(
        conn,
        """
        SELECT data, codigo, fechamento, fechamento_ajustado, retorno_total, provento, volume,
            salto_sem_evento
        FROM mercado.serie_papel WHERE cnpj = :cnpj AND classe = :classe ORDER BY data
        """,
        cnpj=cnpj,
        classe=classe,
    )
    if not serie:
        return None

    indice = 100.0
    for dia in serie:
        if dia["retorno_total"] is not None and not dia["salto_sem_evento"]:
            indice *= 1 + float(dia["retorno_total"])
        dia["retorno_acumulado"] = round(indice, 4)

    documentos = list(
        conn.execute(
            sa.text("SELECT id FROM mercado.documento WHERE cnpj = :cnpj AND tipo = 'DFP'"),
            {"cnpj": cnpj},
        ).scalars()
    )
    return {
        "empresa": next(
            iter(
                _linhas(
                    conn,
                    "SELECT cnpj, razao_social, nome_comercial, setor, situacao, codigo_cvm, "
                    "data_registro, data_cancelamento FROM mercado.empresa WHERE cnpj = :cnpj",
                    cnpj=cnpj,
                )
            ),
            {"cnpj": cnpj},
        ),
        "classe": classe,
        "serie": serie,
        "proventos": _linhas(
            conn,
            """
            SELECT p.data_com, p.tipo, p.valor
            FROM mercado.provento p JOIN mercado.emissor m ON m.codigo = p.emissor
            WHERE m.cnpj = :cnpj AND p.classe = :classe ORDER BY p.data_com DESC
            """,
            cnpj=cnpj,
            classe=classe,
        ),
        "eventos": _linhas(
            conn,
            """
            SELECT e.data_com, e.tipo, e.multiplicador, e.status, 'B3' AS origem
            FROM mercado.evento e JOIN mercado.emissor m ON m.codigo = substr(e.isin, 3, 4)
            WHERE m.cnpj = :cnpj
            UNION ALL
            SELECT data_com, 'INFERIDO', multiplicador, 'inferido', 'IPE' FROM mercado.evento_inferido
            WHERE cnpj = :cnpj
            ORDER BY data_com DESC
            """,
            cnpj=cnpj,
        ),
        "fundamentos": _linhas(
            conn,
            """
            SELECT r.data_referencia, r.receita, r.lucro_liquido, r.lucro_controladores,
                b.patrimonio_controladores, b.caixa, b.divida_bruta
            FROM mercado.fundamento_resultado r
            LEFT JOIN mercado.fundamento_balanco b
                ON b.documento_id = r.documento_id AND b.data = r.data_referencia
            WHERE r.documento_id = ANY(:documentos) AND b.documento_id = ANY(:documentos)
              AND r.inicio_exercicio = make_date(extract(year FROM r.fim_exercicio)::int, 1, 1)
            ORDER BY r.data_referencia
            """,
            documentos=documentos,
        )
        if documentos
        else [],
    }


def alertas(conn: sa.Connection) -> list[dict]:
    rodada = next(
        iter(
            _linhas(
                conn,
                "SELECT iniciada_em, terminada_em, falhas FROM mercado.rodada "
                "ORDER BY iniciada_em DESC LIMIT 1",
            )
        ),
        None,
    )
    ultima = conn.execute(sa.text("SELECT max(data) FROM mercado.cotacao")).scalar()
    agora = datetime.now(UTC)
    return avaliar_alertas(rodada, ultima, agora, agora.astimezone(_BRT).date())


_GUARDADO: dict[str, tuple[float, object]] = {}


def _guardado(chave: str, calcular):
    quando, valor = _GUARDADO.get(chave, (0.0, None))
    if valor is None or time.monotonic() - quando > _VALIDADE_DOS_PAPEIS:
        valor = calcular()
        _GUARDADO[chave] = (time.monotonic(), valor)
    return valor


def visao(conn: sa.Connection) -> dict:
    def calcular() -> dict:
        classes = _linhas(
            conn,
            """
            WITH ultimo AS (SELECT max(data) AS dia FROM mercado.cotacao)
            SELECT 'acao' AS tipo, count(*) AS papeis,
                count(*) FILTER (WHERE ate >= (SELECT dia FROM ultimo) - 10) AS negociando,
                min(desde)::text AS desde
            FROM (SELECT cnpj, classe, min(data) AS desde, max(data) AS ate
                  FROM mercado.serie_papel GROUP BY 1, 2) a
            UNION ALL
            SELECT tipo_ativo, count(*),
                count(*) FILTER (WHERE ate >= (SELECT dia FROM ultimo) - 10), min(desde)::text
            FROM (SELECT tipo_ativo, emissor, classe, min(data) AS desde, max(data) AS ate
                  FROM mercado.serie_fundo GROUP BY 1, 2, 3) f
            GROUP BY tipo_ativo
            """,
        )
        proventos = _linhas(
            conn,
            "SELECT origem, count(*) AS linhas, min(data_com)::text AS desde "
            "FROM mercado.provento GROUP BY origem ORDER BY origem",
        )
        tesouro = _linhas(
            conn,
            "SELECT count(DISTINCT (titulo, vencimento)) AS titulos, min(data)::text AS desde "
            "FROM mercado.tesouro",
        )[0]
        return {"classes": classes, "proventos": proventos, "tesouro": tesouro}

    return _guardado("visao", calcular)


def ativos(conn: sa.Connection) -> list[dict]:
    return _guardado(
        "ativos",
        lambda: _linhas(
            conn,
            """
            SELECT 'acao' AS tipo, p.cnpj AS chave, p.classe, p.codigo, p.ultimo_pregao,
                coalesce(e.nome_comercial, e.razao_social) AS nome, e.setor
            FROM (
                SELECT DISTINCT ON (cnpj, classe) cnpj, classe, codigo, data AS ultimo_pregao
                FROM mercado.serie_papel ORDER BY cnpj, classe, data DESC
            ) p
            LEFT JOIN mercado.empresa e ON e.cnpj = p.cnpj
            UNION ALL
            SELECT f.tipo_ativo, f.emissor, f.classe, f.codigo, f.ultimo_pregao, a.nome_resumido,
                NULL
            FROM (
                SELECT DISTINCT ON (emissor, classe) emissor, classe, tipo_ativo, codigo, isin,
                    data AS ultimo_pregao
                FROM mercado.serie_fundo ORDER BY emissor, classe, data DESC
            ) f
            LEFT JOIN mercado.ativo a ON a.isin = f.isin
            ORDER BY codigo
            """,
        ),
    )


def fundo(conn: sa.Connection, emissor: str, classe: str) -> dict | None:
    serie = _linhas(
        conn,
        """
        SELECT data, codigo, tipo_ativo, isin, retorno_total, salto_sem_evento
        FROM mercado.serie_fundo WHERE emissor = :emissor AND classe = :classe
        ORDER BY data
        """,
        emissor=emissor,
        classe=classe,
    )
    if not serie:
        return None
    indice = 100.0
    for dia in serie:
        if dia["retorno_total"] is not None and not dia["salto_sem_evento"]:
            indice *= 1 + float(dia["retorno_total"])
        dia["retorno_acumulado"] = round(indice, 4)
    ultimo = serie[-1]
    nome = conn.execute(
        sa.text("SELECT nome_resumido FROM mercado.ativo WHERE isin = :isin"),
        {"isin": ultimo["isin"]},
    ).scalar()
    return {
        "emissor": emissor,
        "classe": classe,
        "tipo": ultimo["tipo_ativo"],
        "nome": nome,
        "serie": [
            {k: dia[k] for k in ("data", "codigo", "retorno_acumulado", "salto_sem_evento")}
            for dia in serie
        ],
        "proventos": _linhas(
            conn,
            """
            SELECT data_com, tipo, valor, origem FROM mercado.provento
            WHERE emissor = :emissor AND classe = :classe ORDER BY data_com DESC, origem
            """,
            emissor=emissor,
            classe=classe,
        ),
        "eventos": _linhas(
            conn,
            """
            SELECT e.data_com, e.tipo, e.multiplicador, e.status
            FROM mercado.evento e JOIN mercado.ativo a ON a.isin = e.isin
            WHERE e.emissor = :emissor AND a.especie LIKE :prefixo
            ORDER BY e.data_com DESC
            """,
            emissor=emissor,
            prefixo=f"{classe}%",
        ),
    }


def macro(conn: sa.Connection) -> dict:
    return _guardado(
        "macro",
        lambda: {
            "ptax": _linhas(
                conn,
                """
                SELECT DISTINCT ON (date_trunc('month', data)) data::text, valor
                FROM mercado.indicador WHERE serie = 1
                ORDER BY date_trunc('month', data), data DESC
                """,
            ),
            "selic_meta": _linhas(
                conn,
                "SELECT data::text, valor FROM mercado.indicador WHERE serie = 432 "
                "ORDER BY data DESC LIMIT 1",
            ),
            "tesouro": _linhas(
                conn,
                """
                SELECT titulo, vencimento::text, data::text, taxa_compra, taxa_venda, pu_compra,
                    pu_venda, pu_base
                FROM mercado.tesouro
                WHERE data = (SELECT max(data) FROM mercado.tesouro)
                ORDER BY titulo, vencimento
                """,
            ),
        },
    )
