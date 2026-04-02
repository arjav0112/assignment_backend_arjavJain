from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.record import FinancialRecord
from app.schemas.record import MessageResponse, PaginatedRecordsResponse, RecordCreate, RecordFilter, RecordOut, RecordUpdate


def _record_base_conditions(filters: RecordFilter | None = None) -> list:
    conditions = [FinancialRecord.is_deleted.is_(False)]
    if filters is None:
        return conditions
    if filters.type is not None:
        conditions.append(FinancialRecord.type == filters.type)
    if filters.category:
        conditions.append(FinancialRecord.category == filters.category)
    if filters.start_date is not None:
        conditions.append(FinancialRecord.date >= filters.start_date)
    if filters.end_date is not None:
        conditions.append(FinancialRecord.date <= filters.end_date)
    return conditions


def get_record_by_id(db: Session, record_id: int) -> RecordOut:
    record = db.execute(
        select(FinancialRecord).where(
            FinancialRecord.id == record_id,
            FinancialRecord.is_deleted.is_(False),
        )
    ).scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return RecordOut.model_validate(record)


def list_records(db: Session, filters: RecordFilter) -> PaginatedRecordsResponse:
    conditions = _record_base_conditions(filters)
    offset = (filters.page - 1) * filters.page_size

    items = db.execute(
        select(FinancialRecord)
        .where(*conditions)
        .order_by(FinancialRecord.date.desc(), FinancialRecord.id.desc())
        .offset(offset)
        .limit(filters.page_size)
    ).scalars().all()

    total = db.execute(
        select(func.count()).select_from(FinancialRecord).where(*conditions)
    ).scalar_one()

    return PaginatedRecordsResponse(
        items=[RecordOut.model_validate(item) for item in items],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
    )


def create_record(db: Session, record_in: RecordCreate, created_by: int) -> RecordOut:
    record = FinancialRecord(created_by=created_by, **record_in.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return RecordOut.model_validate(record)


def update_record(db: Session, record_id: int, record_in: RecordUpdate) -> RecordOut:
    record = db.execute(
        select(FinancialRecord).where(
            FinancialRecord.id == record_id,
            FinancialRecord.is_deleted.is_(False),
        )
    ).scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    updates = record_in.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update",
        )

    for field, value in updates.items():
        setattr(record, field, value)

    db.add(record)
    db.commit()
    db.refresh(record)
    return RecordOut.model_validate(record)


def soft_delete_record(db: Session, record_id: int) -> MessageResponse:
    record = db.execute(
        select(FinancialRecord).where(
            FinancialRecord.id == record_id,
            FinancialRecord.is_deleted.is_(False),
        )
    ).scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    record.is_deleted = True
    db.add(record)
    db.commit()
    return MessageResponse(message="Record deleted successfully")
