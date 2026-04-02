from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.database import get_db
from app.schemas.user import Token, UserCreate, UserOut
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    return user_service.register_user(db=db, user_in=user_in)


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Login with email and password",
    description=(
        "Authenticate with your email address and password. "
        "In Swagger UI, the OAuth2 password flow may still submit the standard `username` field under the hood, "
        "but it should be treated as your email address. "
        "Test admin credentials: `admin@finance.com` / `Admin1234`."
    ),
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    user = user_service.authenticate_user(db=db, email=form_data.username, password=form_data.password)
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return Token(access_token=access_token, token_type="bearer", user=UserOut.model_validate(user))
