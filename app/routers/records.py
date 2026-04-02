from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.rbac import require_admin, require_analyst_above, require_any_role
from app.models.user import User
from app.schemas.record import (
    MessageResponse,
    PaginatedRecordsResponse,
    RecordCreate,
    RecordFilter,
    RecordOut,
    RecordUpdate,
)
from app.services import record_service

router = APIRouter(prefix="/records", tags=["records"])


@router.get("", response_model=PaginatedRecordsResponse)
async def list_records(
    _: Annotated[User, Depends(require_any_role)],
    filters: Annotated[RecordFilter, Depends()],
    db: Session = Depends(get_db),
) -> PaginatedRecordsResponse:
    return record_service.list_records(db=db, filters=filters)


@router.get("/{record_id}", response_model=RecordOut)
async def get_record(
    record_id: int,
    _: Annotated[User, Depends(require_any_role)],
    db: Session = Depends(get_db),
) -> RecordOut:
    return record_service.get_record_by_id(db=db, record_id=record_id)


@router.post("", response_model=RecordOut, status_code=status.HTTP_201_CREATED)
async def create_record(
    record_in: RecordCreate,
    current_user: Annotated[User, Depends(require_analyst_above)],
    db: Session = Depends(get_db),
) -> RecordOut:
    return record_service.create_record(db=db, record_in=record_in, created_by=current_user.id)


@router.put("/{record_id}", response_model=RecordOut)
async def update_record(
    record_id: int,
    record_in: RecordUpdate,
    _: Annotated[User, Depends(require_analyst_above)],
    db: Session = Depends(get_db),
) -> RecordOut:
    return record_service.update_record(db=db, record_id=record_id, record_in=record_in)


@router.delete("/{record_id}", response_model=MessageResponse)
async def delete_record(
    record_id: int,
    _: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> MessageResponse:
    return record_service.soft_delete_record(db=db, record_id=record_id)
