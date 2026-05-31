"""Authentication endpoints."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(LoginRequest):
    name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    if not payload.password:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return TokenResponse(access_token="stub-token")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest) -> TokenResponse:
    return TokenResponse(access_token="stub-token")


@router.post("/forgot-password")
async def forgot_password(email: EmailStr) -> dict[str, str]:
    return {"status": "sent", "email": email}


@router.post("/logout")
async def logout() -> dict[str, str]:
    return {"status": "logged_out"}
