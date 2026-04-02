from __future__ import annotations

from datetime import date as DateType
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.record import RecordType


class TrendPeriod(str, Enum):
    weekly = "weekly"
    monthly = "monthly"


class RecordBase(BaseModel):
    amount: float = Field(gt=0)
    type: RecordType
    category: str = Field(min_length=1, max_length=100)
    date: DateType
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("date")
    @classmethod
    def validate_date_not_in_future(cls, value: DateType) -> DateType:
        if value > DateType.today():
            raise ValueError("Date must not be in the future.")
        return value


class RecordCreate(RecordBase):
    pass


class RecordUpdate(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    type: RecordType | None = None
    category: str | None = Field(default=None, min_length=1, max_length=100)
    date: DateType | None = None
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("date")
    @classmethod
    def validate_optional_date_not_in_future(cls, value: DateType | None) -> DateType | None:
        if value is not None and value > DateType.today():
            raise ValueError("Date must not be in the future.")
        return value


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    type: RecordType
    category: str
    date: DateType
    notes: str | None
    created_by: int | None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class RecordFilter(BaseModel):
    type: RecordType | None = None
    category: str | None = None
    start_date: DateType | None = None
    end_date: DateType | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)

    @model_validator(mode="after")
    def validate_date_range(self) -> "RecordFilter":
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be less than or equal to end_date.")
        return self


class PaginatedRecordsResponse(BaseModel):
    items: list[RecordOut]
    total: int
    page: int
    page_size: int


class SummaryOut(BaseModel):
    total_income: float
    total_expenses: float
    net_balance: float
    total_records: int


class CategorySummaryItem(BaseModel):
    category: str
    total: float
    count: int


class CategoriesResponse(BaseModel):
    categories: list[CategorySummaryItem]


class TrendItem(BaseModel):
    period: str
    income: float
    expenses: float
    net: float


class TrendsResponse(BaseModel):
    trends: list[TrendItem]


class MessageResponse(BaseModel):
    message: str
