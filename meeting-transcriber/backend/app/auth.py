"""Authentication: bcrypt password hashing, JWT creation/verification, FastAPI dependencies."""

from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import get_settings
from app.database import get_user_by_id

security = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: int, username: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_EXPIRE_DAYS)
    payload = {"user_id": user_id, "username": username, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Decode JWT and load full user row from DB. Raises 401 if user missing or soft-deleted.

    Does not check approval status — used for endpoints that must work for pending/revoked
    users too (e.g. /api/auth/me).
    """
    payload = decode_token(credentials.credentials)
    user = await get_user_by_id(payload["user_id"])
    if not user or user["status"] == "deleted":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_user(user: dict = Depends(get_authenticated_user)) -> dict:
    """Require an approved user. Raises 403 'account_not_approved' otherwise."""
    if user["status"] != "approved":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="account_not_approved")
    return user


async def get_admin_user(user: dict = Depends(get_current_user)) -> dict:
    """Require the configured admin user. Raises 403 otherwise."""
    admin_username = get_settings().ADMIN_USERNAME
    if not admin_username or user["username"] != admin_username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin_only")
    return user


def get_user_from_ws_token(token: str) -> dict:
    """Decode JWT from WebSocket query param. Returns payload. Caller enforces status."""
    return decode_token(token)
