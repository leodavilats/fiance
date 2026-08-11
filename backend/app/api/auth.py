from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import (
    get_current_user,
    issue_access_token,
    upsert_user_from_google,
    verify_google_id_token,
)
from app.core.database import SessionLocal
from app.models.db_models import User

router = APIRouter()


class GoogleLoginRequest(BaseModel):
    id_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: str


class LoginResponse(BaseModel):
    access_token: str
    user: UserResponse


@router.post("/auth/google", response_model=LoginResponse)
async def login_with_google(body: GoogleLoginRequest) -> LoginResponse:
    google_user = verify_google_id_token(body.id_token)
    user = upsert_user_from_google(google_user)
    access_token = issue_access_token(user.id)
    return LoginResponse(
        access_token=access_token,
        user=UserResponse(id=user.id, email=user.email, name=user.name, picture=user.picture),
    )


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
