"""Minimal mock bearer-token auth for the POC.

Tokens are just `"token_" + user_id` — good enough to demonstrate the
frontend/backend contract locally. Replace with real JWT/OAuth (and HTTPS)
before this goes anywhere near production.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.models import User, UserRole
from app.store import store

_bearer = HTTPBearer(auto_error=False)


def issue_token(user_id: str) -> str:
    return f"token_{user_id}"


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> User:
    if credentials is None or not credentials.credentials.startswith("token_"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or invalid authorization token")
    user_id = credentials.credentials.removeprefix("token_")
    user = store.get_user(user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown user for token")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin role required")
    return user
