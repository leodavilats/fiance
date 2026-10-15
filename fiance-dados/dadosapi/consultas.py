from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

import sqlalchemy as sa

INDICADORES = {
    "cdi": (12, "CDI diário, % ao dia"),
    "selic": (11, "Selic diária, % ao dia"),
    "selic_meta": (432, "Meta da Selic, % ao ano"),
    "selic_mensal": (4189, "Selic acumulada no mês, anualizada, % ao ano"),
    "ipca": (433, "IPCA mensal, %"),
    "ptax": (1, "Dólar PTAX de venda, R$"),
}

_CLASSE = r"substring(a.especie FROM '^([A-Z0-9]+)')"


def _simples(valor):
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, date | datetime):
        return valor.isoformat()
    return valor


def _linhas(conn: sa.Connection, sql: str, **parametros) -> list[dict]:
    return [
        {k: _simples(v) for k, v in r._mapping.items()}
        for r in conn.execute(sa.text(sql), parametros)
    ]


def _pagina(linhas: list[dict], limite: int, campo: str) -> tuple[list[dict], str | None]:
    if len(linhas) <= limite:
        return linhas, None
    return linhas[:limite], str(linhas[limite - 1][campo])


@dataclass(frozen=True)
class Papel:
    codigo: str
    isin: str
    emissor: str
    classe: str
    cnpj: str | None

    @property
    def e_fundo(self) -> bool:
        return self.classe == "CI" or self.classe.startswith("DR")


def papel(conn: sa.Connection, codigo: str) -> Papel | None:
    linha = conn.execute(
        sa.text(
            f"""
            SELECT t.codigo, t.isin, substr(t.isin, 3, 4) AS emissor, {_CLASSE} AS classe, m.cnpj
            FROM mercado.ticker t
            JOIN mercado.ativo a ON a.isin = t.isin
            LEFT JOIN mercado.emissor m ON m.codigo = substr(t.isin, 3, 4)
            WHERE t.codigo = :codigo
            ORDER BY t.ultimo_pregao DESC LIMIT 1
            """
        ),
        {"codigo": codigo.upper()},
    ).first()
    if linha is None or linha.classe is None:
        return None
    return Papel(linha.codigo, linha.isin, linha.emissor, linha.classe, linha.cnpj)


def ativos(
    conn: sa.Connection, tipo: str | None, busca: str | None, cursor: str | None, limite: int
) -> tuple[list[dict], str | None]:
    linhas = _linhas(
        conn,
        """
        SELECT codigo, tipo, classe, nome, setor, data AS ultimo_pregao, preco, volume_medio
        FROM mercado.ativo_hoje
        WHERE (CAST(:tipo AS text) IS NULL OR tipo = :tipo)
          AND (CAST(:busca AS text) IS NULL OR codigo ILIKE :padrao OR nome ILIKE :padrao)
          AND codigo > :cursor
        ORDER BY codigo LIMIT :n
        """,
        tipo=tipo,
        busca=busca,
        padrao=f"%{busca}%" if busca else None,
        cursor=cursor or "",
        n=limite + 1,
    )
    return _pagina(linhas, limite, "codigo")


def ativo(conn: sa.Connection, codigo: str) -> dict | None:
    hoje = _linhas(
        conn,
        """
        SELECT codigo, isin, tipo, emissor, classe, nome, setor, cnpj, data AS ultimo_pregao,
            preco, preco_anterior, maxima_52s, minima_52s, volume_medio, acoes_ordinarias,
            acoes_preferenciais, valor_patrimonial_cota, referencia_cota, proventos_12m
        FROM mercado.ativo_hoje WHERE codigo = :codigo
        """,
        codigo=codigo.upper(),
    )
    if hoje:
        return {**hoje[0], "negociando": True}
    antigo = _linhas(
        conn,
        f"""
        SELECT t.codigo, t.isin, substr(t.isin, 3, 4) AS emissor, {_CLASSE} AS classe,
            a.nome_resumido AS nome, t.primeiro_pregao, t.ultimo_pregao
        FROM mercado.ticker t JOIN mercado.ativo a ON a.isin = t.isin
        WHERE t.codigo = :codigo ORDER BY t.ultimo_pregao DESC LIMIT 1
        """,
        codigo=codigo.upper(),
    )
    return {**antigo[0], "negociando": False} if antigo else None


_RETRATO = """
SELECT codigo, isin, tipo, emissor, classe, nome, setor, cnpj, data, preco, preco_anterior,
    maxima_52s, minima_52s, volume_medio, acoes_ordinarias, acoes_preferenciais,
    valor_patrimonial_cota, referencia_cota, proventos_12m
FROM mercado.ativo_hoje
"""


def retratos(conn: sa.Connection, codigos: list[str], desde: date) -> dict[str, dict]:
    ativos = _linhas(conn, _RETRATO + " WHERE codigo = ANY(:codigos)", codigos=codigos)
    cnpjs = sorted({a["cnpj"] for a in ativos if a["tipo"] == "stock" and a["cnpj"]})
    irmaos: dict[str, list[dict]] = {}
    demonstracoes: dict[str, list[dict]] = {}
    if cnpjs:
        for linha in _linhas(
            conn,
            "SELECT cnpj, codigo, classe, preco, volume_medio FROM mercado.ativo_hoje "
            "WHERE cnpj = ANY(:cnpjs) ORDER BY codigo",
            cnpjs=cnpjs,
        ):
            irmaos.setdefault(linha.pop("cnpj"), []).append(linha)
        for linha in _linhas(
            conn,
            """
            SELECT f.cnpj, f.tipo, f.data_referencia, f.versao, d.data_entrega, f.fim_exercicio,
                f.receita, f.lucro_controladores, f.patrimonio_controladores, f.divida_bruta
            FROM mercado.fundamento_app f
            JOIN mercado.documento d ON d.cnpj = f.cnpj AND d.tipo = f.tipo
                AND d.data_referencia = f.data_referencia AND d.versao = f.versao
            WHERE f.cnpj = ANY(:cnpjs) AND f.data_referencia >= :desde
            ORDER BY f.cnpj, f.tipo, f.data_referencia, f.versao
            """,
            cnpjs=cnpjs,
            desde=desde,
        ):
            demonstracoes.setdefault(linha.pop("cnpj"), []).append(linha)
    return {
        a["codigo"]: {
            "ativo": a,
            "irmaos": irmaos.get(a["cnpj"], []) if a["tipo"] == "stock" else [],
            "demonstracoes": demonstracoes.get(a["cnpj"], []) if a["tipo"] == "stock" else [],
        }
        for a in ativos
    }


def cotacoes(
    conn: sa.Connection, codigo: str, de: date, ate: date, cursor: str | None, limite: int
) -> tuple[list[dict], str | None]:
    linhas = _linhas(
        conn,
        """
        SELECT data, abertura / fator_cotacao AS abertura, maxima / fator_cotacao AS maxima,
            minima / fator_cotacao AS minima, media / fator_cotacao AS media,
            fechamento / fator_cotacao AS fechamento, negocios, quantidade, volume
        FROM mercado.cotacao
        WHERE codigo = :codigo AND data BETWEEN :de AND :ate AND data > :cursor
        ORDER BY data LIMIT :n
        """,
        codigo=codigo.upper(),
        de=de,
        ate=ate,
        cursor=date.fromisoformat(cursor) if cursor else date.min,
        n=limite + 1,
    )
    return _pagina(linhas, limite, "data")


def serie(
    conn: sa.Connection, p: Papel, de: date, ate: date, cursor: str | None, limite: int
) -> tuple[list[dict], str | None]:
    if p.e_fundo:
        tabela, filtro, chave = "mercado.serie_fundo", "emissor = :chave", p.emissor
        extra = ", provento_estimado"
    else:
        if p.cnpj is None:
            return [], None
        tabela, filtro, chave, extra = "mercado.serie_papel", "cnpj = :chave", p.cnpj, ""
    linhas = _linhas(
        conn,
        f"""
        SELECT data, codigo, fechamento, fator_ajuste, fechamento_ajustado, provento{extra},
            retorno_total, dias_desde_anterior, salto_sem_evento
        FROM {tabela}
        WHERE {filtro} AND classe = :classe AND data BETWEEN :de AND :ate AND data > :cursor
        ORDER BY data LIMIT :n
        """,
        chave=chave,
        classe=p.classe,
        de=de,
        ate=ate,
        cursor=date.fromisoformat(cursor) if cursor else date.min,
        n=limite + 1,
    )
    return _pagina(linhas, limite, "data")


def proventos(conn: sa.Connection, p: Papel, desde: date, incluir_estimados: bool) -> list[dict]:
    return _linhas(
        conn,
        """
        SELECT data_com, data_pagamento, tipo, valor, origem, origem = 'cvm_estimado' AS estimado
        FROM mercado.provento
        WHERE emissor = :emissor AND classe = :classe AND data_com >= :desde
          AND (:estimados OR origem <> 'cvm_estimado')
        ORDER BY data_com, origem
        """,
        emissor=p.emissor,
        classe=p.classe,
        desde=desde,
        estimados=incluir_estimados,
    )


def eventos(conn: sa.Connection, p: Papel, desde: date) -> list[dict]:
    return _linhas(
        conn,
        f"""
        SELECT e.data_com, e.tipo, e.fator, e.multiplicador, e.status, e.data_aprovacao, e.isin
        FROM mercado.evento e JOIN mercado.ativo a ON a.isin = e.isin
        WHERE e.emissor = :emissor AND {_CLASSE} = :classe AND e.data_com >= :desde
        ORDER BY e.data_com
        """,
        emissor=p.emissor,
        classe=p.classe,
        desde=desde,
    )


def empresa(conn: sa.Connection, cnpj: str) -> dict | None:
    linhas = _linhas(
        conn,
        """
        SELECT cnpj, razao_social, nome_comercial, setor, situacao, codigo_cvm, data_registro,
            data_cancelamento
        FROM mercado.empresa WHERE cnpj = :cnpj
        """,
        cnpj=cnpj,
    )
    if not linhas:
        return None
    tickers = _linhas(
        conn,
        "SELECT codigo, classe, tipo FROM mercado.ativo_hoje WHERE cnpj = :cnpj ORDER BY codigo",
        cnpj=cnpj,
    )
    return {**linhas[0], "tickers": tickers}


def demonstracoes(
    conn: sa.Connection, cnpj: str, tipo: str | None, desde: date, sabido_em: date | None
) -> list[dict]:
    return _linhas(
        conn,
        """
        SELECT DISTINCT ON (f.tipo, f.data_referencia)
            f.tipo, f.data_referencia, f.versao, d.data_entrega, f.receita, f.lucro_controladores,
            f.patrimonio_controladores, f.divida_bruta
        FROM mercado.fundamento_app f
        JOIN mercado.documento d ON d.cnpj = f.cnpj AND d.tipo = f.tipo
            AND d.data_referencia = f.data_referencia AND d.versao = f.versao
        WHERE f.cnpj = :cnpj AND (CAST(:tipo AS text) IS NULL OR f.tipo = :tipo)
          AND f.data_referencia >= :desde
          AND (CAST(:sabido_em AS date) IS NULL OR d.data_entrega <= :sabido_em)
        ORDER BY f.tipo, f.data_referencia, f.versao DESC
        """,
        cnpj=cnpj,
        tipo=tipo,
        desde=desde,
        sabido_em=sabido_em,
    )


def informes_de_fii(conn: sa.Connection, p: Papel, desde: date) -> list[dict]:
    return _linhas(
        conn,
        """
        SELECT referencia, cnpj, nome, segmento, mandato, valor_patrimonial_cota,
            patrimonio_liquido, cotas_emitidas, dividend_yield_mes
        FROM mercado.fii_mensal
        WHERE emissor = :emissor AND classe = :classe AND referencia >= :desde
        ORDER BY referencia
        """,
        emissor=p.emissor,
        classe=p.classe,
        desde=desde,
    )


def indicador(
    conn: sa.Connection, serie_: int, de: date, ate: date, cursor: str | None, limite: int
) -> tuple[list[dict], str | None]:
    linhas = _linhas(
        conn,
        """
        SELECT data, valor FROM mercado.indicador
        WHERE serie = :serie AND data BETWEEN :de AND :ate AND data > :cursor
        ORDER BY data LIMIT :n
        """,
        serie=serie_,
        de=de,
        ate=ate,
        cursor=date.fromisoformat(cursor) if cursor else date.min,
        n=limite + 1,
    )
    return _pagina(linhas, limite, "data")


def tesouro_hoje(conn: sa.Connection) -> list[dict]:
    return _linhas(
        conn,
        """
        SELECT titulo, vencimento, data, taxa_compra, taxa_venda, pu_compra, pu_venda, pu_base
        FROM mercado.tesouro WHERE data = (SELECT max(data) FROM mercado.tesouro)
        ORDER BY titulo, vencimento
        """,
    )


def tesouro_historico(
    conn: sa.Connection,
    titulo: str,
    vencimento: date,
    de: date,
    ate: date,
    cursor: str | None,
    limite: int,
) -> tuple[list[dict], str | None]:
    linhas = _linhas(
        conn,
        """
        SELECT data, taxa_compra, taxa_venda, pu_compra, pu_venda, pu_base
        FROM mercado.tesouro
        WHERE titulo = :titulo AND vencimento = :vencimento AND data BETWEEN :de AND :ate
          AND data > :cursor
        ORDER BY data LIMIT :n
        """,
        titulo=titulo,
        vencimento=vencimento,
        de=de,
        ate=ate,
        cursor=date.fromisoformat(cursor) if cursor else date.min,
        n=limite + 1,
    )
    return _pagina(linhas, limite, "data")


def atualidade(conn: sa.Connection) -> dict:
    datas = _linhas(
        conn,
        """
        SELECT (SELECT max(data) FROM mercado.cotacao) AS cotacao,
            (SELECT max(data_entrega) FROM mercado.documento) AS demonstracao,
            (SELECT max(data_com) FROM mercado.provento WHERE origem <> 'cvm_estimado') AS provento,
            (SELECT max(data) FROM mercado.tesouro) AS tesouro,
            (SELECT max(referencia) FROM mercado.fii_mensal) AS informe_de_fii
        """,
    )[0]
    rodada = _linhas(
        conn,
        "SELECT iniciada_em, terminada_em, falhas FROM mercado.rodada "
        "ORDER BY iniciada_em DESC LIMIT 1",
    )
    return {"ate": datas, "ultima_coleta": rodada[0] if rodada else None}
