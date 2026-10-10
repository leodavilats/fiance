from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from datajob import coleta
from datajob.esquema import cotacao
from datajob.fontes import b3_cotahist
from datajob.rede import Ausente

PRIMEIRO_ANO = 2005

_LACUNA_PARA_O_ANUAL = timedelta(days=10)

_BRT = ZoneInfo("America/Sao_Paulo")


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


def ultimo_pregao_gravado(engine: sa.Engine) -> date | None:
    with engine.connect() as conn:
        return conn.execute(sa.select(sa.func.max(cotacao.c.data))).scalar_one()


def diario(
    engine: sa.Engine,
    raiz: Path,
    baixar: Callable[[str], bytes],
    relatar: Callable[[str, coleta.Resultado | None], None],
    hoje: date | None = None,
) -> None:
    urls = pendencias(ultimo_pregao_gravado(engine), hoje or hoje_no_brasil())
    for url in urls:
        nome = url.rsplit("/", 1)[1]
        try:
            conteudo = baixar(url)
        except Ausente:
            relatar(nome, None)
            continue
        relatar(
            nome,
            coleta.executar(engine, raiz, b3_cotahist.FONTE, nome, conteudo, b3_cotahist.processar),
        )
