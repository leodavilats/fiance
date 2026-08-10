from __future__ import annotations

import time

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import get_settings
from app.core.context import set_current_user_id
from app.core.database import SessionLocal, init_db
from app.models.db_models import User

JWT_ALGORITHM = "HS256"
JWT_TTL_SECONDS = 30 * 24 * 3600

_bearer = HTTPBearer(auto_error=False)

_initialized = False


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
        # audience=None pula a checagem automática — o app tem client IDs
        # diferentes para Android e iOS, então validamos o aud manualmente.
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


def issue_access_token(user_id: str) -> str:
    settings = get_settings()
    now = int(time.time())
    payload = {"sub": user_id, "iat": now, "exp": now + JWT_TTL_SECONDS}
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def upsert_user_from_google(google_user: GoogleUser) -> User:
    global _initialized
    if not _initialized:
        init_db()
        _initialized = True

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
        session.commit()
        session.refresh(user)
        return user
    finally:
        session.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticação necessária"
        )

    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials, settings.jwt_secret, algorithms=[JWT_ALGORITHM]
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada") from exc

    user_id = payload["sub"]
    set_current_user_id(user_id)
    return user_id
