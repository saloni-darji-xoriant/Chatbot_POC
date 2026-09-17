from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user, issue_token
from app.models import LoginRequest, LoginResponse, SsoLoginRequest, User
from app.store import store

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Log in with a work email and password",
)
def login(payload: LoginRequest) -> LoginResponse:
    entry = store.get_user_by_email(payload.email)
    if entry is None or entry["password"] != payload.password:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    user: User = entry["user"]
    return LoginResponse(token=issue_token(user.id), user=user)


@router.post(
    "/sso",
    response_model=LoginResponse,
    summary="Log in via Company SSO (mocked)",
    description="In production this would redirect to the corporate IdP. "
    "For this POC it resolves a user directly from the email domain.",
)
def sso_login(payload: SsoLoginRequest) -> LoginResponse:
    entry = store.get_user_by_email(payload.email)
    if entry is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No account found for that email")
    user: User = entry["user"]
    return LoginResponse(token=issue_token(user.id), user=user)


@router.get("/me", response_model=User, summary="Get the current authenticated user")
def me(user: User = Depends(get_current_user)) -> User:
    return user
