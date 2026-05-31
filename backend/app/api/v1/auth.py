"""Authentication endpoints — email/password + Google OAuth."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.dependencies import get_db, require_user
from app.models.user import User

logger = logging.getLogger("screen-finance.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginIn(BaseModel):
    credential: str = Field(description="Google ID token (JWT) from GIS")


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    is_admin: bool = False
    provider: str = "local"
    avatar_url: str | None = None

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


def _issue_token(user: User) -> TokenOut:
    token = create_access_token(
        subject=user.id,
        extra={"email": user.email, "is_admin": user.is_admin},
    )
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterIn, db: AsyncSession = Depends(get_db)) -> TokenOut:
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")

    user = User(
        email=payload.email,
        name=payload.name.strip(),
        password_hash=hash_password(payload.password),
        provider="local",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _issue_token(user)


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, db: AsyncSession = Depends(get_db)) -> TokenOut:
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is disabled")
    return _issue_token(user)


@router.post("/google", response_model=TokenOut)
async def google_login(payload: GoogleLoginIn, db: AsyncSession = Depends(get_db)) -> TokenOut:
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Google sign-in is not configured on the server (missing GOOGLE_CLIENT_ID).",
        )

    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token as google_id_token
    except ImportError as exc:
        logger.error("google-auth not installed: %s", exc)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Google auth library unavailable") from exc

    try:
        info = google_id_token.verify_oauth2_token(
            payload.credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as exc:
        logger.warning("Invalid Google ID token: %s", exc)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Google credential") from exc

    google_sub = info.get("sub")
    email = info.get("email")
    if not google_sub or not email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Google token missing required claims")
    if not info.get("email_verified", False):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Google email is not verified")

    user = await db.scalar(select(User).where(User.google_id == google_sub))
    if user is None:
        user = await db.scalar(select(User).where(User.email == email))
        if user is not None:
            user.google_id = google_sub
            if user.provider == "local":
                user.provider = "google"
            user.avatar_url = user.avatar_url or info.get("picture")
        else:
            user = User(
                email=email,
                name=info.get("name") or email.split("@")[0],
                password_hash=None,
                provider="google",
                google_id=google_sub,
                avatar_url=info.get("picture"),
            )
            db.add(user)

    await db.commit()
    await db.refresh(user)
    return _issue_token(user)


@router.get("/me", response_model=UserOut)
async def me(current=Depends(require_user)) -> UserOut:
    return UserOut.model_validate(current)


@router.post("/logout")
async def logout() -> dict[str, str]:
    """Stateless JWT logout — the client just discards the token."""
    return {"status": "logged_out"}
