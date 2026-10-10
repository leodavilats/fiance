from __future__ import annotations

import json
import sys
import time
import traceback
from collections.abc import Callable
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from datajob import armazenamento, coleta, emissores, inferencia
from datajob.esquema import cotacao, documento, indicador, valor_mobiliario
from datajob.fontes import (
    b3_cotahist,
    b3_emissores,
    b3_proventos,
    bcb_sgs,
    cvm_cadastro,
    cvm_demonstracoes,
    cvm_fca,
    cvm_ipe,
)
from datajob.rede import Ausente

PRIMEIRO_ANO = 2005

_LACUNA_PARA_O_ANUAL = timedelta(days=10)

_BRT = ZoneInfo("America/Sao_Paulo")

_SEXTA = 4
PAUSA_ENTRE_EMISSORES = 0.5

Relatar = Callable[[str, coleta.Resultado | None], None]


def hoje_no_brasil() -> date:
    return datetime.now(_BRT).date()


def pendencias(ultimo: date | None, hoje: date) -> list[str]:
    if ultimo is None or ultimo.year < hoje.year:
        inicio = PRIMEIRO_ANO if ultimo is None else ultimo.year
        return [b3_cotahist.url_do_ano(ano) for ano in range(inicio, hoje.year + 1)]
    if hoje - ultimo > _LACUNA_PARA_O_ANUAL:
        return [b3_cotahist.url_do_ano(hoje.year)]
    dias = (ultimo + timedelta(days=n) for n in range(1, (hoje - ultimo).days + 1))
    return [b3_cotahist.url_do_dia(dia) for dia in dias if dia.weekday() < 5]


def anos_do_fca(tem_fca: bool, hoje: date) -> list[int]:
    inicio = hoje.year - 1 if tem_fca else cvm_fca.PRIMEIRO_ANO
    return list(range(inicio, hoje.year + 1))


def anos_de_demonstracao(tipo: str, tem_documento: bool, hoje: date) -> list[int]:
    inicio = hoje.year - 1 if tem_documento else cvm_demonstracoes.PRIMEIRO_ANO[tipo]
    return list(range(inicio, hoje.year + 1))


def _tem_documento(engine: sa.Engine, tipo: str) -> bool:
    with engine.connect() as conn:
        consulta = sa.select(documento.c.id).where(documento.c.tipo == tipo).limit(1)
        return conn.execute(consulta).first() is not None


def _ultima_data(engine: sa.Engine, serie: int) -> date | None:
    with engine.connect() as conn:
        consulta = sa.select(sa.func.max(indicador.c.data)).where(indicador.c.serie == serie)
        return conn.execute(consulta).scalar_one()


def proventos_hoje(tem_provento: bool, hoje: date) -> bool:
    return not tem_provento or hoje.weekday() == _SEXTA


def _tem_provento(engine: sa.Engine) -> bool:
    with engine.connect() as conn:
        return conn.execute(sa.text("SELECT 1 FROM mercado.provento LIMIT 1")).first() is not None


def anos_do_ipe(tem_ipe: bool, hoje: date) -> list[int]:
    inicio = hoje.year - 1 if tem_ipe else cvm_ipe.PRIMEIRO_ANO
    return list(range(inicio, hoje.year + 1))


def _tem_ipe(engine: sa.Engine) -> bool:
    with engine.connect() as conn:
        return (
            conn.execute(sa.text("SELECT 1 FROM mercado.ipe_documento LIMIT 1")).first() is not None
        )


def ultimo_pregao_gravado(engine: sa.Engine) -> date | None:
    with engine.connect() as conn:
        return conn.execute(sa.select(sa.func.max(cotacao.c.data))).scalar_one()


def _tem_fca(engine: sa.Engine) -> bool:
    with engine.connect() as conn:
        return conn.execute(sa.select(valor_mobiliario.c.cnpj).limit(1)).first() is not None


def _arquivo(engine, raiz, relatar, baixar, fonte, url, processar, nome=None) -> None:
    nome = nome or url.rsplit("/", 1)[1]
    try:
        conteudo = baixar(url)
    except Ausente:
        relatar(nome, None)
        return
    relatar(nome, coleta.executar(engine, raiz, fonte, nome, conteudo, processar))


def diario(
    engine: sa.Engine,
    raiz: Path,
    baixar: Callable[[str], bytes],
    relatar: Relatar,
    hoje: date | None = None,
) -> list[str]:
    hoje = hoje or hoje_no_brasil()

    def cotahist() -> None:
        for url in pendencias(ultimo_pregao_gravado(engine), hoje):
            _arquivo(engine, raiz, relatar, baixar, b3_cotahist.FONTE, url, b3_cotahist.processar)

    def cadastro() -> None:
        _arquivo(
            engine,
            raiz,
            relatar,
            baixar,
            cvm_cadastro.FONTE,
            cvm_cadastro.URL,
            cvm_cadastro.processar,
        )

    def fca() -> None:
        for ano in anos_do_fca(_tem_fca(engine), hoje):
            url = cvm_fca.url_do_ano(ano)
            _arquivo(engine, raiz, relatar, baixar, cvm_fca.FONTE, url, cvm_fca.processar)

    def emissores_b3() -> None:
        conteudo = b3_emissores.baixar_lista(baixar)
        relatar(
            b3_emissores.NOME,
            coleta.executar(
                engine,
                raiz,
                b3_emissores.FONTE,
                b3_emissores.NOME,
                conteudo,
                b3_emissores.processar,
            ),
        )

    def ligar_emissores() -> None:
        with engine.begin() as conn:
            contagem = emissores.recalcular(conn)
        print(f"emissores ligados a CNPJ: {dict(contagem)}", flush=True)

    def demonstracoes() -> None:
        for tipo in ("DFP", "ITR"):
            processar = cvm_demonstracoes.processador(tipo)
            for ano in anos_de_demonstracao(tipo, _tem_documento(engine, tipo), hoje):
                url = cvm_demonstracoes.url_do_ano(tipo, ano)
                _arquivo(
                    engine, raiz, relatar, baixar, cvm_demonstracoes.FONTE[tipo], url, processar
                )

    def series_do_bcb() -> None:
        for serie in bcb_sgs.SERIES:
            processar = bcb_sgs.processador(serie)
            for inicio, fim in bcb_sgs.janelas(_ultima_data(engine, serie), hoje):
                _arquivo(
                    engine,
                    raiz,
                    relatar,
                    baixar,
                    bcb_sgs.FONTE,
                    bcb_sgs.url(serie, inicio, fim),
                    processar,
                    nome=bcb_sgs.nome(serie, inicio, fim),
                )

    def proventos_e_eventos() -> None:
        if not proventos_hoje(_tem_provento(engine), hoje):
            print("proventos e eventos da B3: só às sextas.", flush=True)
            return
        with engine.connect() as conn:
            codigos = conn.execute(
                sa.text("SELECT codigo FROM mercado.emissor ORDER BY 1")
            ).scalars()
            codigos = list(codigos)
        falharam = []
        for codigo in codigos:
            nome = f"b3_proventos_{codigo}.json"
            try:
                try:
                    conteudo = b3_proventos.baixar_emissor(codigo, baixar)
                except Ausente:
                    relatar(nome, None)
                    continue
                if not json.loads(conteudo)["nome_pregao"]:
                    relatar(nome, None)
                    continue
                relatar(
                    nome,
                    coleta.executar(
                        engine, raiz, b3_proventos.FONTE, nome, conteudo, b3_proventos.processar
                    ),
                )
            except Exception as e:
                falharam.append(codigo)
                print(f"Falhou ({nome}): {type(e).__name__}: {e}", file=sys.stderr, flush=True)
            time.sleep(PAUSA_ENTRE_EMISSORES)
        if falharam:
            raise RuntimeError(
                f"{len(falharam)} emissores sem proventos: {', '.join(falharam[:20])}"
            )

    def ipe() -> None:
        for ano in anos_do_ipe(_tem_ipe(engine), hoje):
            url = cvm_ipe.url_do_ano(ano)
            _arquivo(engine, raiz, relatar, baixar, cvm_ipe.FONTE, url, cvm_ipe.processar)

    def composicao_do_bruto() -> None:
        with engine.connect() as conn:
            vazia = conn.execute(
                sa.text("SELECT 1 FROM mercado.composicao_capital LIMIT 1")
            ).first()
        if vazia is not None:
            return
        for tipo in ("DFP", "ITR"):
            for caminho in armazenamento.guardados(raiz, cvm_demonstracoes.FONTE[tipo]):
                with engine.begin() as conn:
                    linhas = cvm_demonstracoes.gravar_composicao(conn, caminho.read_bytes(), tipo)
                print(f"composição do capital de {caminho.name}: {linhas} linhas.", flush=True)

    def recalcular_serie() -> None:
        inicio = time.monotonic()
        with engine.begin() as conn:
            conn.execute(sa.text("REFRESH MATERIALIZED VIEW mercado.serie_papel"))
        print(f"série ajustada recalculada em {time.monotonic() - inicio:.0f} s.", flush=True)

    def serie_ajustada() -> None:
        recalcular_serie()
        with engine.begin() as conn:
            inferidos = inferencia.inferir(conn)
        print(f"eventos inferidos de saltos com documento no IPE: {inferidos}.", flush=True)
        if inferidos:
            recalcular_serie()

    falhas = []
    etapas = {
        "cotações da B3": cotahist,
        "cadastro da CVM": cadastro,
        "FCA da CVM": fca,
        "emissores da B3": emissores_b3,
        "ligação emissor-CNPJ": ligar_emissores,
        "DFP e ITR da CVM": demonstracoes,
        "séries do BCB": series_do_bcb,
        "proventos e eventos da B3": proventos_e_eventos,
        "IPE da CVM": ipe,
        "composição do capital": composicao_do_bruto,
        "série ajustada": serie_ajustada,
    }
    for nome, etapa in etapas.items():
        try:
            etapa()
        except Exception as e:
            falhas.append(nome)
            print(f"Falhou ({nome}): {type(e).__name__}: {e}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
    return falhas
