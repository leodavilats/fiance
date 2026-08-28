"""Indicação: código, atribuição e crédito.

Um programa de indicação é a única aquisição que cabe neste produto. Mídia paga
está fora de alcance por aritmética — R$ 500 a R$ 1.500 por instalação
qualificada em finanças no Brasil, contra um teto de CAC de R$ 72 —, então o
canal que sobra é alguém contando para alguém. O programa existe para tornar
isso um pouco mais provável, não para comprar cadastro.

É por isso que a regra central deste módulo é **quando** o crédito sai, não
quanto ele vale:

* Cadastro é grátis de fabricar aos milhares. Se o crédito saísse na criação da
  conta, o programa seria uma máquina de imprimir Premium apontada para o
  próprio caixa, e a primeira pessoa a perceber isso não seria a gente.
* Carteira salva, não. O crédito sai quando quem foi indicado salva a primeira
  posição — o mesmo marco que dispara o trial, porque é o mesmo sinal de que
  ali tem uma pessoa de verdade.

O resto são cercas contra os abusos óbvios: ninguém se indica, ninguém é
atribuído duas vezes, e ninguém é atribuído depois de já estar usando o
produto.
"""

from __future__ import annotations

import logging
import secrets
import time
import uuid

from sqlalchemy import select

from app.core.database import db_session
from app.models.db_models import PortfolioPosition, ReferralCodeDb, ReferralDb, SubscriptionDb
from app.storage import audit_store, event_store, portfolio_store

logger = logging.getLogger("fiance.referral")

#: Dias de Premium por indicação qualificada, para cada lado.
#:
#: Vale para os dois porque o convite precisa ser bom de fazer e bom de aceitar:
#: um programa só para quem indica é um pedido de favor. Sessenta dias somados
#: custam ~R$ 4 de infraestrutura contra um teto de CAC de R$ 72 — cabe com
#: folga, e é o que torna este canal viável onde mídia paga não é.
REWARD_DAYS = 30

#: Teto de crédito acumulado por pessoa, em dias.
#:
#: Crédito sem teto é passivo sem teto. E quem traz duzentas pessoas não precisa
#: de dezesseis anos de Premium: precisa de uma conversa de parceria, que é
#: decisão comercial e não consequência automática de um contador.
MAX_CREDITED_DAYS = 365

#: Alfabeto sem os pares que se confundem lidos em voz alta ou copiados de uma
#: captura de tela: O/0, I/1/L. Código de indicação é dito por WhatsApp.
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_CODE_LENGTH = 8


class ReferralError(ValueError):
    """Atribuição recusada, com o motivo já em português."""


def _generate_code() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(_CODE_LENGTH))


def code_for(user_id: str) -> str:
    """O código da pessoa, criando-o na primeira vez. Idempotente."""
    with db_session() as session:
        row = session.get(ReferralCodeDb, user_id)
        if row is not None:
            return row.code

        portfolio_store.ensure_user(session, user_id)

        # Colisão é improvável (31^8) mas não impossível, e um código duplicado
        # atribuiria a indicação à pessoa errada — falha silenciosa e cara.
        for _ in range(10):
            candidato = _generate_code()
            existe = session.execute(
                select(ReferralCodeDb).where(ReferralCodeDb.code == candidato)
            ).scalar_one_or_none()
            if existe is None:
                session.add(ReferralCodeDb(user_id=user_id, code=candidato, created_at=time.time()))
                return candidato

        raise ReferralError("Não foi possível gerar um código. Tente de novo.")


def rotate_code(user_id: str) -> str:
    """Queima o código atual e devolve outro.

    Existe porque um link publicado em grupo que virou spam não deveria custar
    a conta. As indicações já atribuídas guardam o código usado e não são
    afetadas.
    """
    with db_session() as session:
        row = session.get(ReferralCodeDb, user_id)
        if row is not None:
            session.delete(row)
            session.flush()
    return code_for(user_id)


def _owner_of(session, code: str) -> str | None:
    row = session.execute(
        select(ReferralCodeDb).where(ReferralCodeDb.code == code.strip().upper())
    ).scalar_one_or_none()
    return row.user_id if row else None


def attribute(user_id: str, code: str, now: float | None = None) -> dict:
    """Registra que ``user_id`` chegou pelo código de outra pessoa.

    Não concede nada: a concessão é em `qualify`. Aqui só se decide de quem é o
    crédito, e as recusas são todas do mesmo tipo — impedir que a atribuição
    seja fabricada.
    """
    moment = now if now is not None else time.time()
    limpo = (code or "").strip().upper()
    if not limpo:
        raise ReferralError("Código vazio.")

    with db_session() as session:
        dono = _owner_of(session, limpo)
        if dono is None:
            raise ReferralError("Código de indicação não encontrado.")

        if dono == user_id:
            # Auto-indicação é o primeiro abuso que qualquer pessoa tenta, e é
            # o mais barato de bloquear.
            raise ReferralError("Você não pode usar o próprio código.")

        ja = session.execute(
            select(ReferralDb).where(ReferralDb.referred_user_id == user_id)
        ).scalar_one_or_none()
        if ja is not None:
            raise ReferralError("Esta conta já foi atribuída a uma indicação.")

        # Atribuição só antes de a conta ter história. Aceitar depois deixaria
        # qualquer pessoa reivindicar um usuário que já estava no produto — o
        # crédito sairia de uma aquisição que não aconteceu.
        tem_carteira = session.execute(
            select(PortfolioPosition.ticker).where(PortfolioPosition.user_id == user_id).limit(1)
        ).first()
        if tem_carteira is not None:
            raise ReferralError(
                "Esta conta já tem carteira. A indicação só vale para quem está chegando."
            )

        portfolio_store.ensure_user(session, user_id)
        registro = ReferralDb(
            id=uuid.uuid4().hex,
            user_id=dono,
            referred_user_id=user_id,
            code=limpo,
            created_at=moment,
        )
        session.add(registro)
        resultado = {"referrer_user_id": dono, "code": limpo, "created_at": moment}

    event_store.record(user_id, "referral_attributed", {}, platform="server")
    return resultado


def _credit(session, user_id: str, days: int, moment: float) -> int:
    """Soma dias de Premium a quem já pode ter crédito correndo.

    Estende a partir do fim vigente, não de agora: creditar a partir de hoje
    apagaria o saldo de quem indicou duas pessoas na mesma semana.
    """
    row = session.get(SubscriptionDb, user_id)
    if row is None:
        portfolio_store.ensure_user(session, user_id)
        row = SubscriptionDb(user_id=user_id, created_at=moment, updated_at=moment)
        session.add(row)
        session.flush()

    restante = MAX_CREDITED_DAYS - row.credited_days_total
    concedidos = max(0, min(days, restante))
    if concedidos == 0:
        return 0

    base = max(moment, row.credited_until or 0.0)
    row.credited_until = base + concedidos * 86400
    row.credited_days_total += concedidos
    row.updated_at = moment
    return concedidos


def qualify(referred_user_id: str, now: float | None = None) -> dict | None:
    """A indicação vira crédito. Chamado quando a pessoa salva a 1ª posição.

    Idempotente: `rewarded_at` já preenchido significa que os dias já saíram, e
    creditar de novo é o modo de falha que ninguém percebe até a fatura.
    """
    moment = now if now is not None else time.time()

    with db_session() as session:
        registro = session.execute(
            select(ReferralDb).where(ReferralDb.referred_user_id == referred_user_id)
        ).scalar_one_or_none()
        if registro is None or registro.rewarded_at is not None:
            return None

        registro.qualified_at = moment
        registro.rewarded_at = moment
        registro.reward_days = REWARD_DAYS

        # O id sai da sessão junto com os números: usar `registro` depois do
        # `with` estouraria `DetachedInstanceError` na hora de gravar o evento.
        indicador = registro.user_id
        ao_indicador = _credit(session, indicador, REWARD_DAYS, moment)
        ao_indicado = _credit(session, referred_user_id, REWARD_DAYS, moment)

        resultado = {
            "referrer_user_id": indicador,
            "referred_user_id": referred_user_id,
            "referrer_days": ao_indicador,
            "referred_days": ao_indicado,
        }

    event_store.record(indicador, "referral_qualified", {}, platform="server")
    audit_store.write(
        audit_store.REFERRAL_REWARD,
        entity="referral",
        summary=f"Indicação qualificada: {ao_indicador} dia(s) de crédito.",
        user_id=indicador,
    )
    return resultado


def status(user_id: str) -> dict:
    """O que a pessoa vê: o código, quantas indicações e quanto crédito.

    Nunca a lista de quem foi indicado. Quem clicou no seu link não escolheu
    aparecer numa tela sua, e a contagem já basta para o programa funcionar.
    """
    codigo = code_for(user_id)

    with db_session() as session:
        registros = (
            session.execute(select(ReferralDb).where(ReferralDb.user_id == user_id)).scalars().all()
        )
        atribuidas = len(registros)
        qualificadas = sum(1 for r in registros if r.rewarded_at is not None)
        dias = sum(r.reward_days for r in registros if r.rewarded_at is not None)

        assinatura = session.get(SubscriptionDb, user_id)
        credito_ate = assinatura.credited_until if assinatura else None
        credito_total = assinatura.credited_days_total if assinatura else 0

    return {
        "code": codigo,
        "reward_days": REWARD_DAYS,
        "max_credited_days": MAX_CREDITED_DAYS,
        "attributed": atribuidas,
        # A diferença entre as duas contagens é a informação útil: quem clicou
        # mas não montou carteira ainda é a pessoa a quem lembrar.
        "qualified": qualificadas,
        "pending": atribuidas - qualificadas,
        "days_earned": dias,
        "credited_until": credito_ate,
        "credited_days_total": credito_total,
    }
