from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.rbac import require_any_role
from app.models.record import RecordType
from app.models.user import User
from app.schemas.record import CategoriesResponse, RecordOut, SummaryOut, TrendPeriod, TrendsResponse
from app.services import analytics_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=SummaryOut)
async def get_summary(
    _: Annotated[User, Depends(require_any_role)],
    db: Session = Depends(get_db),
    start_date: date | None = None,
    end_date: date | None = None,
) -> SummaryOut:
    return analytics_service.get_summary(db=db, start_date=start_date, end_date=end_date)


@router.get("/categories", response_model=CategoriesResponse)
async def get_categories(
    _: Annotated[User, Depends(require_any_role)],
    db: Session = Depends(get_db),
    type: RecordType | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> CategoriesResponse:
    return analytics_service.get_categories_breakdown(
        db=db,
        record_type=type,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/trends", response_model=TrendsResponse)
async def get_trends(
    _: Annotated[User, Depends(require_any_role)],
    db: Session = Depends(get_db),
    period: TrendPeriod = Query(default=TrendPeriod.monthly),
) -> TrendsResponse:
    return analytics_service.get_trends(db=db, period=period)


@router.get("/recent", response_model=list[RecordOut])
async def get_recent_records(
    _: Annotated[User, Depends(require_any_role)],
    db: Session = Depends(get_db),
    limit: int = Query(default=5, ge=1, le=20),
) -> list[RecordOut]:
    return analytics_service.get_recent_records(db=db, limit=limit)
