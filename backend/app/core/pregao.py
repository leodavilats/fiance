"""A janela em que o preço se move.

Separado de `core/brt.py` de propósito: lá mora o **fuso fiscal**, que decide mês de apuração e
faixa de alíquota. Aqui mora o **horário do mercado**, que decide quando vale gastar cota da
fonte. São dois calendários diferentes, e juntá-los faria uma mudança de pregão mexer em IR.
"""

from __future__ import annotations

from datetime import datetime, time

from app.core.brt import now_brt

ABERTURA = time(10, 0)

# O fim da janela é 18h30, e não 17h30: o último preço do dia assenta depois do leilão de
# fechamento, e balanço na B3 costuma sair **depois** do pregão. Uma janela que fecha junto com o
# mercado perderia as duas coisas e só as leria às 10h do dia seguinte.
FECHAMENTO = time(18, 30)


def em_pregao(momento: datetime | None = None) -> bool:
    """Se o mercado está aberto, ou na hora que o segue.

    O instante é parâmetro para que o teste não dependa do relógio de quem o roda: regra de
    horário sem injeção é suíte que passa às 14h e falha às 3h.

    **Não conhece feriado da B3.** Não há calendário no produto, e uma lista fixa de datas
    envelheceria calada. O custo é cerca de doze varreduras por ano em dia sem pregão, contra a
    manutenção anual de uma constante que ninguém lembraria de revisar.
    """
    agora = momento or now_brt()

    if agora.weekday() >= 5:
        return False

    return ABERTURA <= agora.time() <= FECHAMENTO
