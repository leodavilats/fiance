from __future__ import annotations

import time
import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core import sessions
from app.core.config import get_settings
from app.core.context import set_current_user_id
from app.core.database import SessionLocal, ensure_initialized
from app.models.db_models import User

JWT_ALGORITHM = "HS256"

# TTL curto no token de acesso e um refresh longo: é o que permite que
# "sair" tenha efeito de servidor sem manter uma denylist do tamanho da base.
ACCESS_TTL_SECONDS = 60 * 60
REFRESH_TTL_SECONDS = 30 * 24 * 3600

# Compatibilidade: o emissor antigo assinava 30 dias sem `typ` nem `jti`.
# Esses tokens continuam valendo como acesso até expirarem — só não são
# revogáveis individualmente, porque não têm identidade.
LEGACY_ACCESS_TYP = "access"

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

# Claims sem as quais o token não é sequer considerado. Antes disso, um token
# sem `sub` estourava KeyError e virava 500 — erro de autenticação tem que
# responder 401.
REQUIRED_CLAIMS = ["sub", "exp", "iat"]

_bearer = HTTPBearer(auto_error=False)


class GoogleUser:
    def __init__(self, sub: str, email: str, name: str, picture: str):
        self.sub = sub
        self.email = email
        self.name = name
        self.picture = picture


def verify_google_id_token(token: str) -> GoogleUser:
    settings = get_settings()
    allowed_client_ids = settings.google_client_ids
    if not allowed_client_ids:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID não configurado")

    try:
        payload = google_id_token.verify_oauth2_token(token, google_requests.Request())
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Token do Google inválido: {exc}") from exc

    if payload.get("aud") not in allowed_client_ids:
        raise HTTPException(status_code=401, detail="Token do Google com audience não reconhecida")

    return GoogleUser(
        sub=payload["sub"],
        email=payload.get("email", ""),
        name=payload.get("name", ""),
        picture=payload.get("picture", ""),
    )


def _issue(user_id: str, typ: str, ttl_seconds: int) -> str:
    settings = get_settings()
    # `iat` com precisão fracionária de propósito: o corte de revogação em bloco
    # compara contra ele, e truncar ao segundo faria um token emitido logo depois
    # de um "sair de todos" nascer morto — ou um token emitido logo antes
    # sobreviver. NumericDate admite fração; só nós lemos esta claim.
    now = time.time()
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": int(now) + ttl_seconds,
        "jti": uuid.uuid4().hex,
        "typ": typ,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def issue_access_token(user_id: str) -> str:
    return _issue(user_id, TOKEN_TYPE_ACCESS, ACCESS_TTL_SECONDS)


def issue_refresh_token(user_id: str) -> str:
    return _issue(user_id, TOKEN_TYPE_REFRESH, REFRESH_TTL_SECONDS)


def decode_token(token: str, expected_typ: str) -> dict:
    """Decodifica exigindo as claims obrigatórias e o tipo certo.

    Levanta 401 em qualquer falha — inclusive claim ausente, tipo trocado,
    `jti` revogado e token emitido antes de uma revogação em bloco.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[JWT_ALGORITHM],
            options={"require": REQUIRED_CLAIMS},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada") from exc

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada")

    typ = payload.get("typ", LEGACY_ACCESS_TYP)
    if typ != expected_typ:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada")

    jti = payload.get("jti")
    if isinstance(jti, str) and jti and sessions.is_revoked(jti):
        raise HTTPException(status_code=401, detail="Sessão encerrada")

    issued_at = float(payload.get("iat") or 0)
    if issued_at < sessions.tokens_valid_from(user_id):
        raise HTTPException(status_code=401, detail="Sessão encerrada")

    return payload


def revoke_token(payload: dict) -> None:
    """Coloca o token do payload na denylist até o seu próprio `exp`."""
    jti = payload.get("jti")
    if not isinstance(jti, str) or not jti:
        return
    sessions.revoke_jti(jti, payload["sub"], float(payload.get("exp") or 0))


def upsert_user_from_google(google_user: GoogleUser) -> User:
    ensure_initialized()

    session = SessionLocal()
    try:
        user = session.get(User, google_user.sub)
        if user is None:
            user = User(
                id=google_user.sub,
                email=google_user.email,
                name=google_user.name,
                picture=google_user.picture,
            )
            session.add(user)
        else:
            user.email = google_user.email
            user.name = google_user.name
            user.picture = google_user.picture
            # Voltar depois de excluir a conta é começar de novo, não recuperar:
            # os dados já foram embora e a lápide sai do caminho.
            user.deleted_at = None
        session.commit()
        session.refresh(user)
        return user
    finally:
        session.close()


async def get_access_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticação necessária"
        )

    payload = decode_token(credentials.credentials, TOKEN_TYPE_ACCESS)
    set_current_user_id(payload["sub"])
    return payload


async def get_current_user(payload: dict = Depends(get_access_payload)) -> str:
    return payload["sub"]


async def require_admin(user_id: str = Depends(get_current_user)) -> str:
    settings = get_settings()
    admins = settings.admin_ids

    if not admins:
        if settings.is_development:
            return user_id
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rota de manutenção indisponível: ADMIN_USER_IDS não configurado.",
        )

    if user_id not in admins:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rota restrita a operadores.",
        )
    return user_id
