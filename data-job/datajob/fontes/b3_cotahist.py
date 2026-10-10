from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

import sqlalchemy as sa

FONTE = "b3_cotahist"

_BASE = "https://bvmf.bmfbovespa.com.br/InstDados/SerHist"

_TAMANHO_DO_REGISTRO = 245
_MERCADO_A_VISTA = "010"


class ArquivoInvalido(ValueError):
    pass


def url_do_ano(ano: int) -> str:
    return f"{_BASE}/COTAHIST_A{ano}.ZIP"


def url_do_dia(dia: date) -> str:
    return f"{_BASE}/COTAHIST_D{dia:%d%m%Y}.ZIP"


@dataclass(frozen=True)
class Cotacao:
    isin: str
    data: date
    codigo: str
    codbdi: str
    nome_resumido: str
    especie: str
    abertura: Decimal
    maxima: Decimal
    minima: Decimal
    media: Decimal
    fechamento: Decimal
    negocios: int
    quantidade: int
    volume: Decimal
    fator_cotacao: int


@dataclass(frozen=True)
class Rejeitada:
    chave: str
    motivo: str
    conteudo: str


@dataclass
class Leitura:
    registros: int = 0
    cotacoes: list[Cotacao] = field(default_factory=list)
    rejeitadas: list[Rejeitada] = field(default_factory=list)


def texto_do_zip(conteudo: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(conteudo)) as arquivo:
            nomes = [n for n in arquivo.namelist() if not n.endswith("/")]
            if len(nomes) != 1:
                raise ArquivoInvalido(f"O ZIP deveria ter um arquivo, e tem {len(nomes)}.")
            return arquivo.read(nomes[0]).decode("latin-1")
    except zipfile.BadZipFile as e:
        raise ArquivoInvalido("O conteúdo baixado não é um ZIP.") from e


def _preco(campo: str) -> Decimal:
    return Decimal(campo).scaleb(-2)


def _data(campo: str) -> date:
    return date(int(campo[0:4]), int(campo[4:6]), int(campo[6:8]))


def _cotacao(linha: str) -> Cotacao:
    return Cotacao(
        data=_data(linha[2:10]),
        codbdi=linha[10:12],
        codigo=linha[12:24].strip(),
        nome_resumido=linha[27:39].strip(),
        especie=linha[39:49].strip(),
        abertura=_preco(linha[56:69]),
        maxima=_preco(linha[69:82]),
        minima=_preco(linha[82:95]),
        media=_preco(linha[95:108]),
        fechamento=_preco(linha[108:121]),
        negocios=int(linha[147:152]),
        quantidade=int(linha[152:170]),
        volume=_preco(linha[170:188]),
        fator_cotacao=int(linha[210:217]),
        isin=linha[230:242].strip(),
    )


def _implausivel(c: Cotacao) -> str | None:
    if not c.isin:
        return "sem ISIN"
    if c.fator_cotacao <= 0:
        return "fator de cotação não positivo"
    precos = (c.abertura, c.maxima, c.minima, c.media, c.fechamento)
    if any(p <= 0 for p in precos):
        return "preço não positivo"
    if c.minima > c.maxima:
        return "mínima acima da máxima"
    if any(not (c.minima <= p <= c.maxima) for p in (c.abertura, c.fechamento)):
        return "preço fora da faixa do dia"
    if c.negocios < 0 or c.quantidade < 0 or c.volume < 0:
        return "volume negativo"
    return None


def interpretar(texto: str) -> Leitura:
    linhas = texto.splitlines()
    if not linhas or not linhas[0].startswith("00COTAHIST."):
        raise ArquivoInvalido("Falta o registro de cabeçalho do COTAHIST.")
    if not linhas[-1].startswith("99COTAHIST."):
        raise ArquivoInvalido("Falta o registro final: o arquivo chegou cortado.")

    leitura = Leitura()
    vistas: set[tuple[str, date]] = set()
    for numero, linha in enumerate(linhas[1:-1], start=2):
        if len(linha) != _TAMANHO_DO_REGISTRO:
            raise ArquivoInvalido(
                f"Linha {numero} tem {len(linha)} posições, e o registro tem {_TAMANHO_DO_REGISTRO}."
            )
        if not linha.startswith("01"):
            raise ArquivoInvalido(f"Linha {numero} não é registro de cotação.")
        leitura.registros += 1
        if linha[24:27] != _MERCADO_A_VISTA:
            continue

        chave = f"{linha[12:24].strip()} {linha[2:10]}"
        try:
            cotacao = _cotacao(linha)
        except (ValueError, ArithmeticError):
            leitura.rejeitadas.append(Rejeitada(chave, "campo ilegível", linha))
            continue

        motivo = _implausivel(cotacao)
        if motivo is None and (cotacao.isin, cotacao.data) in vistas:
            motivo = "ISIN repetido no mesmo pregão"
        if motivo:
            leitura.rejeitadas.append(Rejeitada(chave, motivo, linha))
            continue

        vistas.add((cotacao.isin, cotacao.data))
        leitura.cotacoes.append(cotacao)

    declarados = int(linhas[-1][31:42])
    if declarados != leitura.registros:
        raise ArquivoInvalido(
            f"O registro final declara {declarados} cotações, e o arquivo tem {leitura.registros}."
        )
    return leitura


_COLUNAS = (
    "isin",
    "data",
    "codigo",
    "codbdi",
    "nome_resumido",
    "especie",
    "abertura",
    "maxima",
    "minima",
    "media",
    "fechamento",
    "negocios",
    "quantidade",
    "volume",
    "fator_cotacao",
)

_CRIAR_CARGA = """
CREATE TEMP TABLE _carga (
    isin text, data date, codigo text, codbdi text, nome_resumido text, especie text,
    abertura numeric, maxima numeric, minima numeric, media numeric, fechamento numeric,
    negocios integer, quantidade bigint, volume numeric, fator_cotacao integer
) ON COMMIT DROP
"""

_GRAVAR_ATIVO = """
INSERT INTO mercado.ativo AS a (isin, nome_resumido, especie, codbdi, primeiro_pregao, ultimo_pregao)
SELECT DISTINCT ON (isin) isin, nome_resumido, especie, codbdi,
       MIN(data) OVER (PARTITION BY isin), MAX(data) OVER (PARTITION BY isin)
FROM _carga
ORDER BY isin, data DESC
ON CONFLICT (isin) DO UPDATE SET
    nome_resumido = CASE WHEN EXCLUDED.ultimo_pregao >= a.ultimo_pregao
                         THEN EXCLUDED.nome_resumido ELSE a.nome_resumido END,
    especie = CASE WHEN EXCLUDED.ultimo_pregao >= a.ultimo_pregao
                   THEN EXCLUDED.especie ELSE a.especie END,
    codbdi = CASE WHEN EXCLUDED.ultimo_pregao >= a.ultimo_pregao
                  THEN EXCLUDED.codbdi ELSE a.codbdi END,
    primeiro_pregao = LEAST(a.primeiro_pregao, EXCLUDED.primeiro_pregao),
    ultimo_pregao = GREATEST(a.ultimo_pregao, EXCLUDED.ultimo_pregao)
WHERE EXCLUDED.primeiro_pregao < a.primeiro_pregao
   OR EXCLUDED.ultimo_pregao > a.ultimo_pregao
   OR (EXCLUDED.ultimo_pregao = a.ultimo_pregao
       AND (EXCLUDED.nome_resumido, EXCLUDED.especie, EXCLUDED.codbdi)
           IS DISTINCT FROM (a.nome_resumido, a.especie, a.codbdi))
"""

_GRAVAR_TICKER = """
INSERT INTO mercado.ticker AS t (codigo, isin, primeiro_pregao, ultimo_pregao)
SELECT codigo, isin, MIN(data), MAX(data) FROM _carga GROUP BY codigo, isin
ON CONFLICT (codigo, isin) DO UPDATE SET
    primeiro_pregao = LEAST(t.primeiro_pregao, EXCLUDED.primeiro_pregao),
    ultimo_pregao = GREATEST(t.ultimo_pregao, EXCLUDED.ultimo_pregao)
WHERE EXCLUDED.primeiro_pregao < t.primeiro_pregao
   OR EXCLUDED.ultimo_pregao > t.ultimo_pregao
"""

_CAMPOS_DE_COTACAO = (
    "codigo, codbdi, abertura, maxima, minima, media, fechamento, "
    "negocios, quantidade, volume, fator_cotacao"
)

_GRAVAR_COTACAO = f"""
INSERT INTO mercado.cotacao AS c (isin, data, {_CAMPOS_DE_COTACAO}, coleta_id)
SELECT isin, data, {_CAMPOS_DE_COTACAO}, :coleta_id FROM _carga
ON CONFLICT (isin, data) DO UPDATE SET
    {", ".join(f"{c} = EXCLUDED.{c}" for c in _CAMPOS_DE_COTACAO.split(", "))},
    coleta_id = EXCLUDED.coleta_id
WHERE ({", ".join(f"c.{c}" for c in _CAMPOS_DE_COTACAO.split(", "))})
      IS DISTINCT FROM
      ({", ".join(f"EXCLUDED.{c}" for c in _CAMPOS_DE_COTACAO.split(", "))})
"""


def gravar(conn: sa.Connection, leitura: Leitura, coleta_id: int) -> int:
    conn.execute(sa.text(_CRIAR_CARGA))
    cursor = conn.connection.driver_connection.cursor()
    with cursor.copy(f"COPY _carga ({', '.join(_COLUNAS)}) FROM STDIN") as copia:
        for c in leitura.cotacoes:
            copia.write_row(tuple(getattr(c, coluna) for coluna in _COLUNAS))

    conn.execute(sa.text(_GRAVAR_ATIVO))
    conn.execute(sa.text(_GRAVAR_TICKER))
    gravadas = conn.execute(sa.text(_GRAVAR_COTACAO), {"coleta_id": coleta_id}).rowcount

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
    return gravadas


def processar(conn: sa.Connection, conteudo: bytes, coleta_id: int) -> tuple[int, int, int]:
    leitura = interpretar(texto_do_zip(conteudo))
    gravadas = gravar(conn, leitura, coleta_id)
    return leitura.registros, gravadas, len(leitura.rejeitadas)
