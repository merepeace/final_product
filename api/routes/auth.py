from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from auth.jwt_handler import create_access_token, verify_admin_credentials
from dependencies import get_current_user
from schemas.auth import CurrentUser, LoginRequest, Token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest):
    """JSON login endpoint used by the React frontend."""
    if not verify_admin_credentials(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return Token(access_token=create_access_token(subject=payload.username))


@router.post("/token", response_model=Token, include_in_schema=False)
def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 password-flow endpoint used by Swagger UI's Authorize button."""
    if not verify_admin_credentials(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return Token(access_token=create_access_token(subject=form_data.username))


@router.get("/me", response_model=CurrentUser)
def me(user: dict = Depends(get_current_user)):
    return CurrentUser(username=user["username"])
