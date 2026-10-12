from __future__ import annotations

import time

import sqlalchemy as sa


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
