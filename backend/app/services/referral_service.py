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

REWARD_DAYS = 30

MAX_CREDITED_DAYS = 365

_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_CODE_LENGTH = 8


class ReferralError(ValueError):
    pass


def _generate_code() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(_CODE_LENGTH))


def code_for(user_id: str) -> str:
    with db_session() as session:
        row = session.get(ReferralCodeDb, user_id)
        if row is not None:
            return row.code

        portfolio_store.ensure_user(session, user_id)

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
    moment = now if now is not None else time.time()
    limpo = (code or "").strip().upper()
    if not limpo:
        raise ReferralError("Código vazio.")

    with db_session() as session:
        dono = _owner_of(session, limpo)
        if dono is None:
            raise ReferralError("Código de indicação não encontrado.")

        if dono == user_id:
            raise ReferralError("Você não pode usar o próprio código.")

        ja = session.execute(
            select(ReferralDb).where(ReferralDb.referred_user_id == user_id)
        ).scalar_one_or_none()
        if ja is not None:
            raise ReferralError("Esta conta já foi atribuída a uma indicação.")

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
        "qualified": qualificadas,
        "pending": atribuidas - qualificadas,
        "days_earned": dias,
        "credited_until": credito_ate,
        "credited_days_total": credito_total,
    }
