"""Marcos de domínio emitidos pelo servidor, não pelo cliente.

Ativação é a métrica que decide o portão G2, e não pode depender de o cliente
lembrar de disparar o evento — nem de qual cliente é. `primeira posição salva` e
`carteira com 4 ativos` acontecem no servidor, então é o servidor que os grava.

São idempotentes por construção: o marco é um `primeiro`, e gravá-lo duas vezes
inflaria a coorte. O gatilho do trial de 14 dias vai pendurar exatamente aqui.
"""

from __future__ import annotations

import logging

from app.core.context import get_current_user_id_or_none
from app.storage import event_store

logger = logging.getLogger("fiance.milestones")

# Mínimo para o veredito de risco ser emitido — e por isso o corte de
# "carteira legível" no funil.
READABLE_PORTFOLIO_SIZE = 4


def _record_once(user_id: str, name: str, props: dict[str, str] | None = None) -> bool:
    if event_store.has_event(user_id, name):
        return False
    event_store.record(user_id, name, props or {}, platform="server")
    return True


def record_portfolio_milestones(position_count: int, user_id: str | None = None) -> None:
    """Grava os marcos de carteira que a contagem atual já satisfaz.

    Nunca deixa uma falha de instrumentação derrubar uma escrita de carteira:
    perder um evento é ruim, perder o aporte do usuário é inaceitável.
    """
    uid = user_id or get_current_user_id_or_none()
    if not uid:
        return

    try:
        if position_count >= 1:
            primeira = _record_once(uid, "portfolio_first_position_added")
            if primeira:
                # O trial começa aqui, e não no cadastro: trial que expira
                # antes de a pessoa ter uma carteira para analisar é trial
                # desperdiçado — ela nunca chega a ver o que estaria comprando.
                from app.services import referral_service, subscription_service

                subscription_service.start_trial(uid)
                # A indicação vira crédito **aqui**, e não no cadastro: conta
                # é grátis de fabricar aos milhares, carteira não é. Sair no
                # cadastro faria do programa uma máquina de imprimir Premium.
                referral_service.qualify(uid)

        if position_count >= READABLE_PORTFOLIO_SIZE:
            _record_once(uid, "portfolio_reached_4_assets")
    except Exception:
        logger.warning("Falha ao gravar marco de carteira para %s", uid, exc_info=True)
