from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import MessageResponse, PaginatedUsersResponse, UserCreate, UserOut, UserUpdate


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> User:
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def create_user(db: Session, user_in: UserCreate) -> UserOut:
    if get_user_by_email(db=db, email=user_in.email) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered")

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


def register_user(db: Session, user_in: UserCreate) -> UserOut:
    return create_user(db=db, user_in=user_in)


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db=db, email=email)
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
    return user


def list_users(db: Session, page: int, page_size: int) -> PaginatedUsersResponse:
    offset = (page - 1) * page_size
    items = db.execute(select(User).order_by(User.id).offset(offset).limit(page_size)).scalars().all()
    total = db.execute(select(func.count()).select_from(User)).scalar_one()
    return PaginatedUsersResponse(
        items=[UserOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def update_user(db: Session, user_id: int, user_in: UserUpdate) -> UserOut:
    user = get_user_by_id(db=db, user_id=user_id)
    updates = user_in.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update",
        )

    for field, value in updates.items():
        setattr(user, field, value)

    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


def delete_user(db: Session, user_id: int, acting_user_id: int) -> MessageResponse:
    if user_id == acting_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admins cannot delete themselves")

    user = get_user_by_id(db=db, user_id=user_id)
    db.delete(user)
    db.commit()
    return MessageResponse(message="User deleted successfully")
