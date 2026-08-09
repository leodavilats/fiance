from fastapi import APIRouter
from pydantic import BaseModel

from app.core.auth import issue_access_token, upsert_user_from_google, verify_google_id_token

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
