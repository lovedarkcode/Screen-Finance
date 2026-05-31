"""FastAPI dependency providers (db sessions, current user, etc.)."""
from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_db() -> AsyncGenerator:
    """Yield an async database session. Wire to SessionLocal in app/db/session.py."""
    yield None


async def get_current_user(token: str | None = Depends(oauth2_scheme)):
    """Resolve the current authenticated user from a JWT (stub)."""
    if token is None:
        return None
    return {"id": "anonymous", "token": token}


async def require_user(user=Depends(get_current_user)):
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return user
