from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import case, extract, func, select
from sqlalchemy.orm import Session

from app.models.record import FinancialRecord, RecordType
from app.schemas.record import (
    CategoriesResponse,
    CategorySummaryItem,
    RecordOut,
    SummaryOut,
    TrendItem,
    TrendPeriod,
    TrendsResponse,
)


def _validate_date_range(start_date: date | None, end_date: date | None) -> None:
    if start_date and end_date and start_date > end_date:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be less than or equal to end_date",
        )


def _dashboard_conditions(
    start_date: date | None = None,
    end_date: date | None = None,
    record_type: RecordType | None = None,
) -> list:
    conditions = [FinancialRecord.is_deleted.is_(False)]
    if record_type is not None:
        conditions.append(FinancialRecord.type == record_type)
    if start_date is not None:
        conditions.append(FinancialRecord.date >= start_date)
    if end_date is not None:
        conditions.append(FinancialRecord.date <= end_date)
    return conditions


def _shift_months(first_day: date, months_back: int) -> date:
    year = first_day.year
    month = first_day.month - months_back
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


def get_summary(db: Session, start_date: date | None, end_date: date | None) -> SummaryOut:
    _validate_date_range(start_date=start_date, end_date=end_date)
    stmt = select(
        func.coalesce(
            func.sum(case((FinancialRecord.type == RecordType.income, FinancialRecord.amount), else_=0.0)),
            0.0,
        ).label("total_income"),
        func.coalesce(
            func.sum(case((FinancialRecord.type == RecordType.expense, FinancialRecord.amount), else_=0.0)),
            0.0,
        ).label("total_expenses"),
        func.count(FinancialRecord.id).label("total_records"),
    ).where(*_dashboard_conditions(start_date=start_date, end_date=end_date))

    totals = db.execute(stmt).one()
    total_income = float(totals.total_income or 0.0)
    total_expenses = float(totals.total_expenses or 0.0)
    return SummaryOut(
        total_income=total_income,
        total_expenses=total_expenses,
        net_balance=total_income - total_expenses,
        total_records=int(totals.total_records or 0),
    )


def get_categories_breakdown(
    db: Session,
    record_type: RecordType | None,
    start_date: date | None,
    end_date: date | None,
) -> CategoriesResponse:
    _validate_date_range(start_date=start_date, end_date=end_date)
    stmt = (
        select(
            FinancialRecord.category.label("category"),
            func.sum(FinancialRecord.amount).label("total"),
            func.count(FinancialRecord.id).label("count"),
        )
        .where(*_dashboard_conditions(start_date=start_date, end_date=end_date, record_type=record_type))
        .group_by(FinancialRecord.category)
        .order_by(func.sum(FinancialRecord.amount).desc(), FinancialRecord.category.asc())
    )
    rows = db.execute(stmt).all()
    return CategoriesResponse(
        categories=[
            CategorySummaryItem(category=row.category, total=float(row.total), count=int(row.count))
            for row in rows
        ]
    )


def get_trends(db: Session, period: TrendPeriod) -> TrendsResponse:
    today = date.today()
    if period == TrendPeriod.monthly:
        current_month = date(today.year, today.month, 1)
        start_period = _shift_months(current_month, 11)
        buckets = [_shift_months(current_month, offset) for offset in range(11, -1, -1)]
        labels = [bucket.strftime("%Y-%m") for bucket in buckets]
        group_year = extract("year", FinancialRecord.date)
        group_part = extract("month", FinancialRecord.date)
    else:
        current_week = today - timedelta(days=today.weekday())
        start_period = current_week - timedelta(weeks=11)
        buckets = [start_period + timedelta(weeks=offset) for offset in range(12)]
        labels = [f"{bucket.isocalendar().year}-W{bucket.isocalendar().week:02d}" for bucket in buckets]
        group_year = extract("isoyear", FinancialRecord.date)
        group_part = extract("week", FinancialRecord.date)

    stmt = (
        select(
            group_year.label("group_year"),
            group_part.label("group_part"),
            func.coalesce(
                func.sum(case((FinancialRecord.type == RecordType.income, FinancialRecord.amount), else_=0.0)),
                0.0,
            ).label("income"),
            func.coalesce(
                func.sum(case((FinancialRecord.type == RecordType.expense, FinancialRecord.amount), else_=0.0)),
                0.0,
            ).label("expenses"),
        )
        .where(*_dashboard_conditions(start_date=start_period))
        .group_by(group_year, group_part)
        .order_by(group_year.asc(), group_part.asc())
    )

    label_map = {label: TrendItem(period=label, income=0.0, expenses=0.0, net=0.0) for label in labels}
    for row in db.execute(stmt).all():
        year = int(row.group_year)
        part = int(row.group_part)
        label = f"{year}-{part:02d}" if period == TrendPeriod.monthly else f"{year}-W{part:02d}"
        if label in label_map:
            income = float(row.income or 0.0)
            expenses = float(row.expenses or 0.0)
            label_map[label] = TrendItem(
                period=label,
                income=income,
                expenses=expenses,
                net=income - expenses,
            )

    return TrendsResponse(trends=[label_map[label] for label in labels])


def get_recent_records(db: Session, limit: int) -> list[RecordOut]:
    records = db.execute(
        select(FinancialRecord)
        .where(FinancialRecord.is_deleted.is_(False))
        .order_by(FinancialRecord.date.desc(), FinancialRecord.id.desc())
        .limit(limit)
    ).scalars().all()
    return [RecordOut.model_validate(record) for record in records]
