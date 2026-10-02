from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.config import settings


# Password hashing using Argon2
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Convert a plain-text password into a secure hash."""
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Check whether a password matches its stored hash."""
    return password_hash.verify(password, hashed_password)


def create_access_token(
    user_id: int,
    expires_minutes: int | None = None,
) -> str:
    """Create a JWT access token for an authenticated user."""

    if expires_minutes is None:
        expires_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""

    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )