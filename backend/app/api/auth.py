import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.core import sessions
from app.core.auth import (
    ACCESS_TTL_SECONDS,
    TOKEN_TYPE_REFRESH,
    decode_token,
    get_access_payload,
    get_current_user,
    issue_access_token,
    issue_refresh_token,
    revoke_token,
    upsert_user_from_google,
    verify_google_id_token,
)
from app.core.database import SessionLocal
from app.core.ratelimit import ip_rate_limit
from app.models.db_models import User
from app.services import referral_service

logger = logging.getLogger("fiance.auth")

router = APIRouter()

AUTH_PER_MINUTE = 20


class GoogleLoginRequest(BaseModel):
    id_token: str
    referral_code: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user: UserResponse


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int


@router.post("/auth/google", response_model=LoginResponse)
async def login_with_google(body: GoogleLoginRequest, request: Request) -> LoginResponse:
    await ip_rate_limit(request, "auth", AUTH_PER_MINUTE)

    google_user = verify_google_id_token(body.id_token)
    user = upsert_user_from_google(google_user)

    if body.referral_code:
        try:
            referral_service.attribute(user.id, body.referral_code)
        except referral_service.ReferralError as erro:
            logger.info("Indicação recusada para %s: %s", user.id, erro)

    return LoginResponse(
        access_token=issue_access_token(user.id),
        refresh_token=issue_refresh_token(user.id),
        expires_in=ACCESS_TTL_SECONDS,
        user=UserResponse(id=user.id, email=user.email, name=user.name, picture=user.picture),
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_session(body: RefreshRequest, request: Request) -> TokenResponse:
    await ip_rate_limit(request, "auth", AUTH_PER_MINUTE)

    payload = decode_token(body.refresh_token, TOKEN_TYPE_REFRESH)
    revoke_token(payload)

    user_id = payload["sub"]
    return TokenResponse(
        access_token=issue_access_token(user_id),
        refresh_token=issue_refresh_token(user_id),
        expires_in=ACCESS_TTL_SECONDS,
    )


class LogoutRequest(BaseModel):
    refresh_token: str | None = None
    all_devices: bool = False


@router.post("/auth/logout")
async def logout(
    body: LogoutRequest | None = None,
    payload: dict = Depends(get_access_payload),
) -> dict:
    body = body or LogoutRequest()

    if body.all_devices:
        sessions.revoke_all_for_user(payload["sub"])
        return {"revoked": "all"}

    revoke_token(payload)
    if body.refresh_token:
        try:
            revoke_token(decode_token(body.refresh_token, TOKEN_TYPE_REFRESH))
        except HTTPException:
            pass
    return {"revoked": "session"}


@router.get("/auth/me", response_model=UserResponse)
async def get_me(user_id: str = Depends(get_current_user)) -> UserResponse:
    session = SessionLocal()
    try:
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        return UserResponse(id=user.id, email=user.email, name=user.name, picture=user.picture)
    finally:
        session.close()
