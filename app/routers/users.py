from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.rbac import require_admin
from app.models.user import User
from app.schemas.user import MessageResponse, PaginatedUsersResponse, UserCreate, UserOut, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=PaginatedUsersResponse)
async def list_users(
    _: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> PaginatedUsersResponse:
    return user_service.list_users(db=db, page=page, page_size=page_size)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    _: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> UserOut:
    return user_service.get_user_by_id(db=db, user_id=user_id)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    _: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> UserOut:
    return user_service.create_user(db=db, user_in=user_in)


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    _: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> UserOut:
    return user_service.update_user(db=db, user_id=user_id, user_in=user_in)


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> MessageResponse:
    return user_service.delete_user(db=db, user_id=user_id, acting_user_id=current_user.id)
