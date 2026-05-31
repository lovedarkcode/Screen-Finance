"""High-level authentication helpers used by services / endpoints."""
from __future__ import annotations

from app.core.security import create_access_token, hash_password, verify_password


class AuthError(Exception):
    pass


def authenticate(email: str, password: str, stored_hash: str | None) -> str:
    if not stored_hash or not verify_password(password, stored_hash):
        raise AuthError("Invalid email or password")
    return create_access_token(subject=email)


def register_user(email: str, password: str) -> tuple[str, str]:
    """Returns (password_hash, access_token)."""
    pw_hash = hash_password(password)
    token = create_access_token(subject=email)
    return pw_hash, token
